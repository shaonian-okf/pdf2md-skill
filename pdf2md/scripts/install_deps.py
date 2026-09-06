# -*- coding: utf-8 -*-
"""
install_deps.py —— pdf2md 技能依赖安装脚本（跨平台：Windows / Linux / macOS）
Install dependencies for the pdf2md skill (cross-platform).

功能（Features）：
  1. 安装 Python 依赖（pip install -r requirements.txt）
     / Install Python dependencies via pip
  2. 检测 tesseract 引擎；缺失时按平台给出安装指引
     / Detect the tesseract engine and print platform-specific guidance
  3. 检测 chi_sim（简体中文）/ eng（英文）语言包；缺失时自动下载到技能目录 tessdata/
     / Detect and download missing language data into the skill's tessdata/ folder

用法（Usage）：
  python install_deps.py               # 全部执行 / do everything
  python install_deps.py --skip-pip    # 跳过 Python 依赖安装
  python install_deps.py --skip-tessdata   # 跳过语言包下载
"""

import os
import sys
import shutil
import argparse
import subprocess
import urllib.request

# 仓库根目录（本脚本位于 pdf2md/scripts/ 下，向上回溯二级）
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # pdf2md 技能目录
_REQ_FILE = os.path.join(_REPO_ROOT, 'requirements.txt')
_TESSDATA_DIR = os.path.join(_SKILL_DIR, 'tessdata')  # 语言包存放目录

# 语言包下载地址（tesseract-ocr/tessdata 官方仓库，兼容 tesseract 4/5）
_LANG_FILES = {
    'chi_sim': 'chi_sim.traineddata',
    'eng': 'eng.traineddata',
}
_BASE_URL = 'https://github.com/tesseract-ocr/tessdata/raw/main/'

# 常见安装路径（Windows / Linux）
_TESSERACT_CANDIDATES = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    r'D:\Program Files\Tesseract-OCR\tesseract.exe',
    '/usr/bin/tesseract',
    '/usr/local/bin/tesseract',
    '/opt/tesseract/bin/tesseract',
]


def info(msg_zh, msg_en):
    """双语输出 / bilingual output."""
    print(f'[>{msg_zh} / {msg_en}]')


def setup_utf8_stdout():
    """控制台 UTF-8 输出，避免 Windows 部分代码页下中文乱码."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass


def ok(msg_zh, msg_en):
    """双语成功输出 / bilingual success output."""
    print(f'[OK] {msg_zh} / {msg_en}')


def fail(msg_zh, msg_en):
    """双语警告输出 / bilingual warning output."""
    print(f'[!!] {msg_zh} / {msg_en}')


def find_tesseract():
    """查找 tesseract 可执行文件：环境变量 → 系统路径 → 常见安装路径."""
    env_path = os.environ.get('TESSERACT_PATH')
    if env_path and os.path.isfile(env_path):
        return env_path
    which = shutil.which('tesseract')
    if which:
        return which
    for c in _TESSERACT_CANDIDATES:
        if os.path.isfile(c):
            return c
    return None


def tesseract_install_guide():
    """按平台输出 tesseract 引擎安装指引."""
    if sys.platform.startswith('win'):
        fail('未找到 tesseract：请下载安装 https://github.com/UB-Mannheim/tesseract '
             '（勾选简体中文语言包），或将 TESSERACT_PATH 指向 tesseract.exe',
             'tesseract not found: install from https://github.com/UB-Mannheim/tesseract '
             '(check the Simplified Chinese language pack), or set TESSERACT_PATH')
    elif sys.platform == 'darwin':
        fail('未找到 tesseract：请执行 brew install tesseract tesseract-lang',
             'tesseract not found: run brew install tesseract tesseract-lang')
    else:
        fail('未找到 tesseract：请执行 sudo apt install tesseract-ocr tesseract-ocr-chi-sim '
             '（或其他发行版对应命令）',
             'tesseract not found: run sudo apt install tesseract-ocr tesseract-ocr-chi-sim '
             '(or your distro equivalent)')


def install_pip_requirements():
    """通过 pip 安装 Python 依赖."""
    if not os.path.isfile(_REQ_FILE):
        fail(f'未找到依赖清单：{_REQ_FILE}', f'requirements file not found: {_REQ_FILE}')
        return False
    info('正在通过 pip 安装 Python 依赖...', 'Installing Python dependencies via pip...')
    try:
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', '-r', _REQ_FILE]
        )
        ok('Python 依赖安装完成', 'Python dependencies installed')
        return True
    except subprocess.CalledProcessError:
        fail('pip 安装失败，请检查网络或使用离线安装（见 INSTALL.md）',
             'pip install failed; check network or use offline install (see INSTALL.md)')
        return False


def ensure_language_data():
    """
    确保 chi_sim / eng 语言包可用。
    先检查现有 tessdata 目录（tesseract 旁 + 技能目录），缺失则下载到技能目录 tessdata/。
    """
    missing = list(_LANG_FILES.keys())
    tesseract_exe = find_tesseract()

    search_dirs = [_TESSDATA_DIR]
    if tesseract_exe:
        base = os.path.dirname(tesseract_exe)
        if os.path.isdir(os.path.join(base, 'tessdata')):
            search_dirs.append(os.path.join(base, 'tessdata'))

    for lang_ in list(missing):
        for d in search_dirs:
            if os.path.isfile(os.path.join(d, _LANG_FILES[lang_])):
                missing.remove(lang_)
                break

    if not missing:
        ok('语言包齐全（chi_sim / eng）', 'Language data complete (chi_sim / eng)')
        return

    os.makedirs(_TESSDATA_DIR, exist_ok=True)
    for lang_ in missing:
        url = _BASE_URL + _LANG_FILES[lang_]
        dest = os.path.join(_TESSDATA_DIR, _LANG_FILES[lang_])
        info(f'正在下载语言包 {lang_}...', f'Downloading language data {lang_}...')
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'pdf2md-skill-installer'})
            with urllib.request.urlopen(req, timeout=120) as resp, open(dest, 'wb') as f:
                shutil.copyfileobj(resp, f)
            size = os.path.getsize(dest)
            if size < 1024 * 1024:  # 下载结果小于 1MB 视为异常（可能是错误页面）
                os.remove(dest)
                fail(f'语言包 {lang_} 下载异常，请手动下载后放入 {_TESSDATA_DIR}',
                     f'download of {lang_} failed; place the file manually into {_TESSDATA_DIR}')
            else:
                ok(f'语言包 {lang_} 下载完成（{size // 1024 // 1024} MB）',
                   f'language data {lang_} downloaded ({size // 1024 // 1024} MB)')
        except Exception as exc:
            fail(f'语言包 {lang_} 下载失败：{exc}', f'failed to download {lang_}: {exc}')


def main():
    parser = argparse.ArgumentParser(
        description='pdf2md 技能依赖安装 / Install pdf2md skill dependencies')
    parser.add_argument('--skip-pip', action='store_true', help='跳过 Python 依赖安装')
    parser.add_argument('--skip-tessdata', action='store_true', help='跳过语言包下载')
    args = parser.parse_args()

    setup_utf8_stdout()

    print('=' * 60)
    print('  pdf2md 依赖安装 / Dependency installer')
    print('=' * 60)

    if not args.skip_pip:
        install_pip_requirements()
    else:
        info('已跳过 Python 依赖安装', 'Skipped pip dependency install')

    print('-' * 60)

    tesseract_exe = find_tesseract()
    if tesseract_exe:
        ok(f'已找到 tesseract：{tesseract_exe}', f'tesseract found: {tesseract_exe}')
    else:
        tesseract_install_guide()

    if not args.skip_tessdata:
        ensure_language_data()
    else:
        info('已跳过语言包下载', 'Skipped language data download')

    print('=' * 60)
    info('安装完成！详见 INSTALL.md 的"验证安装"章节',
         'Done! See "Verify" in INSTALL.md.')
    print('=' * 60)


if __name__ == '__main__':
    main()