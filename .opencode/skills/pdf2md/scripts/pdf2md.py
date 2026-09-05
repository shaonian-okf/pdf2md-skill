# -*- coding: utf-8 -*-
"""
pdf2md.py —— PDF 转完整 Markdown 工具（含图片提取与图片内容 OCR 解析）
pdf2md.py — Convert a PDF into a complete Markdown file (text + images + OCR).

功能（Features）：
  1. 提取 PDF 全部文本内容 / Extract all text
  2. 提取 PDF 内嵌的全部图片（自动按页面位置定位所属章节）
     / Extract all embedded images and keep their layout positions
  3. 对图片进行 OCR（光学字符识别）解析图中文字内容（中英双语识别 chi_sim+eng）
     / OCR image contents (bilingual: Simplified Chinese + English)
  4. 生成完整的 Markdown 文件（正文 + 图片引用 + 图片内容文字解析）

依赖（Dependencies）：
  - pymupdf     （PDF 读取与图片提取）
  - Pillow      （图片预处理）
  - pytesseract （OCR 封装）
  - tesseract   （OCR 引擎，含 chi_sim/eng 语言包）

用法（Usage）：
  python pdf2md.py <输入PDF文件> [输出目录] [--lang zh|en|auto]
  The console messages support Chinese (zh) and English (en);
  --lang auto (default) detects the system language automatically.

示例（Examples）：
  python pdf2md.py 登录系统架构设计.pdf
  python pdf2md.py document.pdf output_folder --lang en
"""

import os
import sys
import shutil
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# 0. 界面语言（中英双语）
# ---------------------------------------------------------------------------

LANG = 'zh'  # 全局界面语言：zh | en，由 --lang 解析后在 main() 中赋值

_MSGS = {
    'zh': {
        'err_file': '[错误] 找不到文件: {0}',
        'err_pymupdf': '[错误] 缺少 pymupdf 库，请先安装：',
        'hint_pymupdf': '       pip install pymupdf',
        'warn_tesseract': '[警告] 未找到 tesseract.exe，图片内容解析（OCR）将不可用。',
        'warn_tesseract2': '       文本与图片仍会正常导出，仅缺少图片内容的文字解析。',
        'use_tesseract': '[工具] 使用 tesseract: {0}',
        'tessdata': '[工具] tessdata: {0}',
        'lang_added': '[工具] 已补充语言包 {0} -> {1}',
        'extract_text': '[工具] 正在提取 PDF 文本: {0}',
        'pages': '[工具] 共 {0} 页文本',
        'extract_img': '[工具] 正在提取内嵌图片...',
        'imgs': '[工具] 提取到 {0} 张图片 -> {1}',
        'ocr_start': '[工具] 正在进行图片 OCR 内容识别...',
        'ocr_item': '  - 识别 {0} ...',
        'ocr_fail': '    (识别失败: {0})',
        'ocr_skip': '[工具] 跳过 OCR（未找到 tesseract）',
        'gen_md': '[工具] 正在生成 Markdown: {0}',
        'done': '==== 处理完成 ====',
        'md_file': '  Markdown 文件: {0}',
        'img_dir': '  图片目录: {0}',
        'img_count': '  提取图片数量: {0}',
        'ocr_count': '  OCR 识别图片数量: {0}',
    },
    'en': {
        'err_file': '[Error] File not found: {0}',
        'err_pymupdf': '[Error] pymupdf is missing. Install it first:',
        'hint_pymupdf': '       pip install pymupdf',
        'warn_tesseract': '[Warning] tesseract.exe not found; OCR of image contents will be skipped.',
        'warn_tesseract2': '       Text and images are still exported normally.',
        'use_tesseract': '[Tool] Using tesseract: {0}',
        'tessdata': '[Tool] tessdata: {0}',
        'lang_added': '[Tool] Language pack added {0} -> {1}',
        'extract_text': '[Tool] Extracting PDF text: {0}',
        'pages': '[Tool] {0} pages of text',
        'extract_img': '[Tool] Extracting embedded images...',
        'imgs': '[Tool] Extracted {0} image(s) -> {1}',
        'ocr_start': '[Tool] Running OCR on images...',
        'ocr_item': '  - OCR {0} ...',
        'ocr_fail': '    (OCR failed: {0})',
        'ocr_skip': '[Tool] Skipping OCR (tesseract not found)',
        'gen_md': '[Tool] Generating Markdown: {0}',
        'done': '==== Done ====',
        'md_file': '  Markdown file: {0}',
        'img_dir': '  Image directory: {0}',
        'img_count': '  Images extracted: {0}',
        'ocr_count': '  Images OCR-processed: {0}',
    },
}


def L(key):
    """按当前界面语言取消息文本，支持 {0}/{1} 占位符格式化。"""
    return _MSGS[LANG][key]


def resolve_lang(choice):
    """
    解析界面语言：'auto'（默认）时自动检测。
    检测顺序：环境变量 LANG/LC_ALL（Linux/macOS 标准）→
    Windows 用户界面语言 → 默认英文。
    """
    if choice in ('zh', 'en'):
        return choice
    env_lang = (os.environ.get('LANG') or os.environ.get('LC_ALL') or '').lower()
    if env_lang.startswith('zh'):
        return 'zh'
    elif env_lang:
        return 'en'
    if sys.platform.startswith('win'):
        try:
            import ctypes
            uilang = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            # 0x0804 简体中文（zh-CN）、0x0404 繁体中文（zh-TW）、0x0C04 繁体中文（zh-HK）
            if uilang in (0x0804, 0x0404, 0x0C04):
                return 'zh'
        except Exception:
            pass
    return 'en'


def setup_utf8_stdout():
    """将控制台标准输出重配置为 UTF-8，避免 Windows 部分代码页下中文乱码。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 1. 环境依赖检测与 tesseract 自动查找（Windows / Linux / macOS）
# ---------------------------------------------------------------------------

def find_tesseract():
    """自动查找 tesseract 可执行文件。检查顺序：环境变量、系统路径、常见路径。"""
    # 1) 环境变量 TESSERACT_PATH
    env_path = os.environ.get('TESSERACT_PATH')
    if env_path and os.path.isfile(env_path):
        return env_path
    # 2) 系统 PATH
    which = shutil.which('tesseract')
    if which:
        return which
    # 3) Windows / Linux 常见安装路径
    candidates = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'D:\Program Files\Tesseract-OCR\tesseract.exe',
        '/usr/bin/tesseract',
        '/usr/local/bin/tesseract',
        '/opt/tesseract/bin/tesseract',
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    # 4) 在工具周边目录与用户临时目录下搜索 tesseract-extracted
    search_bases = _search_dirs()
    # 兼容历史环境：早期版本将 tesseract 解压到 Windows 用户临时目录；
    # 新环境推荐改用环境变量 TESSERACT_PATH 指向 tesseract 可执行文件。
    if sys.platform.startswith('win'):
        legacy = os.path.expanduser('~') + r'\AppData\Local\Temp\opencode'
        if os.path.isdir(legacy):
            search_bases.append(legacy)
    for base in search_bases:
        exe = os.path.join(base, 'tesseract-extracted', 'tesseract.exe')
        if os.path.isfile(exe):
            return exe
    return None


def _search_dirs():
    """返回工具应搜索的目录列表：脚本父目录上级 + 当前工作目录。"""
    here = os.path.dirname(os.path.abspath(__file__))
    dirs = []
    # 脚本所在目录的上级（技能目录内可放置散装资源，如 tesseract-extracted、tessdata）
    parent = os.path.dirname(here)
    if parent and os.path.isdir(parent):
        dirs.append(parent)
    # 当前工作目录
    cwd = str(Path.cwd())
    if cwd not in dirs:
        dirs.append(cwd)
    return dirs


def find_tessdata(tesseract_exe):
    """查找 tessdata 目录（含训练数据）。返回目录路径或 None。"""
    if not tesseract_exe:
        return None
    base = os.path.dirname(tesseract_exe)
    # 1) 相对于 tesseract 可执行文件的 tessdata
    td = os.path.join(base, 'tessdata')
    if os.path.isdir(td):
        return td
    # 2) 在工具周边目录寻找 tessdata
    for p in _search_dirs():
        td = os.path.join(p, 'tessdata')
        if os.path.isdir(td):
            return td
    # 3) 若周边目录有散装 traineddata 文件，则就地当 tessdata
    for p in _search_dirs():
        c = os.path.join(p, 'chi_sim.traineddata')
        e = os.path.join(p, 'eng.traineddata')
        if os.path.isfile(c) or os.path.isfile(e):
            return p
    return None


def ensure_tessdata_languages(tessdata_dir, required=('chi_sim', 'eng')):
    """确保 tessdata 目录包含所需语言包。若缺失则从周边目录补充。"""
    if not tessdata_dir:
        return False
    backup_dirs = _search_dirs()
    for lang_ in required:
        target = os.path.join(tessdata_dir, lang_ + '.traineddata')
        if not os.path.isfile(target):
            for bd in backup_dirs:
                src = os.path.join(bd, lang_ + '.traineddata')
                if os.path.isfile(src):
                    try:
                        shutil.copy2(src, target)
                        print(L('lang_added').format(lang_, target))
                        break
                    except Exception:
                        pass
    # 返回是否齐备
    return all(os.path.isfile(os.path.join(tessdata_dir, l + '.traineddata')) for l in required)


# ---------------------------------------------------------------------------
# 2. PDF 文本提取
# ---------------------------------------------------------------------------

def check_pymupdf():
    """检查 pymupdf 是否可用。"""
    try:
        import pymupdf
        return True, pymupdf
    except ImportError:
        return False, None


def extract_pdf_text(pdf_path):
    """使用 pymupdf 提取 PDF 全文，按页返回文本列表。"""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    pages_text = []
    for page in doc:
        pages_text.append(page.get_text() or '')
    doc.close()
    return pages_text


# ---------------------------------------------------------------------------
# 3. 图片提取与定位
# ---------------------------------------------------------------------------

def extract_images_with_position(pdf_path, out_dir):
    """
    提取 PDF 内嵌图片，并返回每张图片的信息：
      序号、文件名、所在页、页面中的 y 坐标、尺寸、页面文本块（用于定位章节）
    """
    import pymupdf
    doc = pymupdf.open(pdf_path)
    images_info = []

    for pno in range(doc.page_count):
        page = doc[pno]
        # 页面文本块（带 y 坐标），用于判断图片前后的文字位置
        blocks = page.get_text('blocks')
        text_blocks = sorted(
            [b for b in blocks if b[6] == 0],
            key=lambda b: b[1]
        )

        # 遍历页面内嵌图片（get_images 返回 (xref,...)）
        for im in page.get_images():
            xref = im[0]
            w, h = im[2], im[3]
            if w < 30 or h < 30:  # 忽略过小的装饰元素
                continue
            rects = page.get_image_rects(xref)
            if not rects:
                continue
            bbox = rects[0]  # 取第一个区域
            # 提取图片数据
            try:
                img_data = doc.extract_image(xref)
            except Exception:
                continue
            if not img_data:
                continue
            name = f'page{pno+1}_img{len(images_info)+1}.{img_data["ext"]}'
            img_path = os.path.join(out_dir, name)
            with open(img_path, 'wb') as f:
                f.write(img_data['image'])

            images_info.append({
                'file': name,
                'path': img_path,
                'page': pno + 1,
                'y0': bbox.y0,
                'width': w,
                'height': h,
                'text_blocks': text_blocks,
                'size': len(img_data['image']),
                'format': img_data['ext'],
            })

    doc.close()
    return images_info


# ---------------------------------------------------------------------------
# 4. 图片 OCR 识别（中英双语：chi_sim + eng）
# ---------------------------------------------------------------------------

def ocr_image(img_path, tesseract_cmd, tessdata_dir=None):
    """
    对单张图片进行 OCR（光学字符识别），返回识别出的文字。
    内置预处理：放大 3 倍 + 对比度增强，提升识别率。
    """
    import pytesseract
    from PIL import Image, ImageEnhance

    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    if tessdata_dir:
        os.environ['TESSDATA_PREFIX'] = tessdata_dir

    img = Image.open(img_path).convert('L')
    w, h = img.size
    img = img.resize((w * 3, h * 3), Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(2.0)

    # 多种页面分割模式，取有效文字最多的结果
    best = ''
    for psm in (3, 6, 11, 12):
        try:
            text = pytesseract.image_to_string(
                img, lang='chi_sim+eng', config=f'--psm {psm}'
            )
            if len(text.strip()) > len(best.strip()):
                best = text
        except Exception:
            continue
    # 清理纯噪声行（横线、点线等）并整理中文空格
    clean_lines = []
    for ln in best.splitlines():
        s = ln.strip()
        if not s:
            continue
        # 过滤掉几乎全是装饰符的行
        decor = set('-=_—~*·.')
        if len(s) > 5 and all(c in decor for c in s):
            continue
        # 去除中文之间的空格（保留英文单词内部空格）
        s = remove_cn_spaces(s)
        clean_lines.append(s)
    return '\n'.join(clean_lines)


def remove_cn_spaces(text):
    """去除中文之间的空格：'宪 户' -> '宪户'；但保留英文单词内部空格如 'API 网 关' -> 'API 网关'。"""
    import re
    # 规则：当空格两侧至少有一侧是 CJK（中日韩统一表意文字）字符时，删除该空格
    def is_cjk(ch):
        return '\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f'

    chars = list(text)
    result = []
    for i, ch in enumerate(chars):
        if ch in ' \t':
            # 检查前一个和后一个字符
            prev_cjk = i > 0 and is_cjk(chars[i - 1])
            next_cjk = i + 1 < len(chars) and is_cjk(chars[i + 1])
            if prev_cjk or next_cjk:
                continue  # 删除该空格
        result.append(ch)
    return ''.join(result)


def describe_image_by_position(img_info):
    """依据图片在页面中的位置，给出其前后文定位描述（供 md 生成使用）。"""
    pno = img_info['page']
    y0 = img_info['y0']
    below = []  # 图片上方最近的文本（段落引导词）
    above = []  # 图片下方最近的文本
    blocks = img_info['text_blocks']
    for b in blocks:
        by = b[1]
        text = b[4].strip().replace('\n', ' ')
        if by < y0 - 10:
            below.append((by, text))
        elif by > y0 + 10:
            above.append((by, text))
    context = {
        'page': pno,
        'before': below[-2:] if below else [],   # 最近的前文
        'after': above[:2] if above else [],     # 最近的后文
    }
    return context


# ---------------------------------------------------------------------------
# 5. Markdown 生成
# ---------------------------------------------------------------------------

def build_markdown(pdf_path, pages_text, images_info, ocr_results, out_md_path, lang='zh'):
    """
    生成完整 Markdown：正文 + 图片引用 + 图片内容解析。
    图片相对路径统一使用正斜杠 '/'，保证 Windows 与 Linux 渲染一致。
    """
    pdf_name = os.path.basename(pdf_path)
    lines = []
    lines.append(f'# {Path(pdf_name).stem}')
    lines.append('')
    if lang == 'zh':
        lines.append(f'> 来源：{pdf_name}（Source: {pdf_name}）')
        lines.append(f'> 页数：{len(pages_text)}（Pages: {len(pages_text)}）')
        lines.append('> 说明：本文件为 PDF 的完整解析版，包含全部文本内容、内嵌图片及图片内容 OCR 解析。')
    else:
        lines.append(f'> Source: {pdf_name}（来源：{pdf_name}）')
        lines.append(f'> Pages: {len(pages_text)}（页数：{len(pages_text)}）')
        lines.append('> Notes: Full Markdown export of the PDF — all text, embedded images, and OCR of image contents.')
    lines.append('')

    # --- 为每页生成正文，并在图片出现的版面位置插入图片 ---
    import pymupdf
    doc = pymupdf.open(pdf_path)
    for pno in range(len(pages_text)):
        page = doc[pno]
        # 收集本页图片（按 y 坐标排序）
        page_imgs = [im for im in images_info if im['page'] == pno + 1]
        page_imgs.sort(key=lambda im: im['y0'])

        blocks = page.get_text('blocks')
        text_blocks = sorted([b for b in blocks if b[6] == 0], key=lambda b: b[1])

        lines.append(f'## 第 {pno + 1} 页')
        lines.append('')

        # 按 y 坐标合并文本块与图片位置，还原版面顺序
        events = []
        for b in text_blocks:
            events.append((b[1], 'text', b[4].strip()))
        for im in page_imgs:
            events.append((im['y0'], 'image', im))
        events.sort(key=lambda e: e[0])

        for _, etype, data in events:
            if etype == 'text':
                if data:
                    lines.append(data)
                    lines.append('')
            else:
                im = data
                rel = os.path.relpath(im['path'], os.path.dirname(out_md_path))
                rel = rel.replace(os.sep, '/')  # 统一正斜杠，兼容 Win/Linux
                alt = Path(im['file']).stem
                lines.append(f'![{alt}]({rel})')
                lines.append('')
                # 图片内容 OCR 解析
                ocr_txt = ocr_results.get(im['file'], '')
                if ocr_txt.strip():
                    lines.append('**【图片内容解析】**')
                    lines.append('')
                    lines.append('```text')
                    lines.append(ocr_txt)
                    lines.append('```')
                    lines.append('')

    doc.close()
    content = '\n'.join(lines)
    with open(out_md_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return content


# ---------------------------------------------------------------------------
# 6. 主流程
# ---------------------------------------------------------------------------

def main():
    global LANG

    setup_utf8_stdout()

    parser = argparse.ArgumentParser(
        description='PDF 转完整 Markdown（含图片提取与图片 OCR 解析 / with image extraction and OCR）'
    )
    parser.add_argument('pdf', help='输入 PDF 文件路径 / path to the input PDF file')
    parser.add_argument('outdir', nargs='?', default=None,
                        help='输出目录（默认与 PDF 同目录）/ output directory (default: alongside the PDF)')
    parser.add_argument('--lang', choices=['zh', 'en', 'auto'], default='auto',
                        help='界面语言 / console language: zh（中文）、en（English）、auto（自动检测，默认）')
    args = parser.parse_args()

    LANG = resolve_lang(args.lang)

    pdf_path = os.path.abspath(args.pdf)
    if not os.path.isfile(pdf_path):
        print(L('err_file').format(pdf_path))
        sys.exit(1)

    # 输出目录
    if args.outdir:
        out_dir = os.path.abspath(args.outdir)
    else:
        out_dir = os.path.dirname(pdf_path)
    images_dir = os.path.join(out_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)

    pdf_name = os.path.basename(pdf_path)
    md_name = Path(pdf_name).stem + '_完整版.md'
    md_path = os.path.join(out_dir, md_name)

    # ---- 1. 检查 pymupdf ----
    ok, _ = check_pymupdf()
    if not ok:
        print(L('err_pymupdf'))
        print(L('hint_pymupdf'))
        sys.exit(1)

    # ---- 2. 查找 tesseract ----
    tesseract = find_tesseract()
    if not tesseract:
        print(L('warn_tesseract'))
        print(L('warn_tesseract2'))
    else:
        print(L('use_tesseract').format(tesseract))
        td = find_tessdata(tesseract)
        if td:
            ensure_tessdata_languages(td)
            print(L('tessdata').format(td))

    # ---- 3. 提取文本 ----
    print(L('extract_text').format(pdf_name))
    pages_text = extract_pdf_text(pdf_path)
    print(L('pages').format(len(pages_text)))

    # ---- 4. 提取图片 ----
    print(L('extract_img'))
    images_info = extract_images_with_position(pdf_path, images_dir)
    print(L('imgs').format(len(images_info), images_dir))

    # ---- 5. OCR 识别图片 ----
    ocr_results = {}
    if tesseract:
        print(L('ocr_start'))
        for im in images_info:
            print(L('ocr_item').format(im['file']))
            try:
                ocr_results[im['file']] = ocr_image(im['path'], tesseract, td)
            except Exception as e:
                print(L('ocr_fail').format(e))
                ocr_results[im['file']] = ''
    else:
        print(L('ocr_skip'))

    # ---- 6. 生成 Markdown ----
    print(L('gen_md').format(md_path))
    build_markdown(pdf_path, pages_text, images_info, ocr_results, md_path, lang=LANG)

    print('')
    print(L('done'))
    print(L('md_file').format(md_path))
    print(L('img_dir').format(images_dir))
    print(L('img_count').format(len(images_info)))
    print(L('ocr_count').format(len(ocr_results)))


if __name__ == '__main__':
    main()