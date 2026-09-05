---
name: pdf2md
description: 将 PDF 转换为完整、结构清晰的 Markdown 文件（包含全部文本、内嵌图片与图片内容 OCR 解析）。Convert PDF files into complete, well-structured Markdown with full text, embedded images and OCR of image contents. 当用户要求把 PDF 转成 Markdown、提取 PDF 文本或图片、对图片做 OCR 解析时使用。Use when the user asks to convert a PDF to Markdown, extract PDF text or images, or OCR image contents. 触发关键词/Keywords: PDF 转 Markdown、PDF to Markdown、pdf2md、OCR PDF、extract images from PDF。
license: MIT
---

# PDF 转 Markdown（含图片提取与图片文字 OCR）
# PDF to Markdown (with images and OCR)

跨平台（Windows / Linux / macOS）技能，脚本为 Python，Windows 可用 `run.bat`，Linux/macOS 可用 `run.sh` 启动；控制台提示支持中英双语（`--lang zh|en|auto`）。

## 何时使用 / When to use

- 用户要求将 PDF 转成 Markdown 或完整可读的文本版本 / User wants a PDF converted to Markdown or full readable text
- 需要提取 PDF 中的全部内嵌图片，并保留在版面中的原始位置 / Extract all embedded images in their original layout positions
- 需要识别图片或扫描页上的文字（OCR，光学字符识别） / Recognize text inside images or scanned pages (OCR)
- 用户直接提到 pdf2md、PDF 转 Markdown、提取 PDF 图片等关键词 / Keywords: pdf2md, PDF to Markdown, extract PDF images, OCR PDF

## 工作流程 / Workflow

1. **定位技能脚本 / Locate the bundled script**：本技能自带转换脚本，位于技能目录下
   `scripts/pdf2md.py`（即 `<技能目录>/scripts/pdf2md.py`）。若找不到，先用查找工具确认技能目录的实际位置。
   The script ships with this skill at `scripts/pdf2md.py` under the skill directory.

2. **检查依赖 / Check dependencies**（缺失时先安装，命令见"依赖安装"）：
   - Python 3.7 及以上版本 / Python 3.7+
   - pymupdf（PDF 文本与图片提取 / text and image extraction）
   - Pillow（图片预处理 / image preprocessing）与 pytesseract（OCR 封装）
   - tesseract 引擎（外部程序，需含 `chi_sim` 简体中文与 `eng` 英文语言包）。
     脚本自动查找 tesseract：环境变量 `TESSERACT_PATH` → 系统 PATH →
     Windows 与 Linux 常见安装路径 → 技能周边目录。找不到时仍会输出文本与图片，仅跳过 OCR 环节。
     The script auto-locates tesseract via `TESSERACT_PATH` → PATH → common install paths on Windows and Linux.

3. **执行转换 / Run the conversion**：
   ```bash
   python <技能目录>/scripts/pdf2md.py <输入PDF文件> [输出目录] [--lang zh|en|auto]
   ```
   - 输出目录缺省为 PDF 所在目录 / Output dir defaults to the PDF's folder.
   - `--lang` 控制控制台提示语言：`zh`（简体中文）、`en`（English）、`auto`（自动检测，默认）。
     输出 Markdown 的头部"来源/页数"说明为中英双语并列。
   - OCR 语言固定为中英双语识别（`chi_sim+eng`），无需配置。
   - 图片相对路径统一使用正斜杠 `/`，Windows 与 Linux 渲染一致。

4. **校验结果 / Verify output**：确认生成了 `<文件名>_完整版.md` 与 `images/` 图片目录；
   向用户汇报转换结果：Markdown 文件路径、页数、提取图片数量、OCR 识别图片数量。
   Confirm the Markdown file and `images/` folder were created, then report the results.

## 输出规范（脚本已实现）/ Output conventions (implemented)

- Markdown 结构：一级标题（文档名）、来源/页数说明（中英双语）、每页一个 `## 第 N 页` 小节
- 正文按页面内文本块与图片块的纵向坐标合并排序，还原版面阅读顺序
- 图片以相对路径插入对应版面位置，图片下方附 `**【图片内容解析】**` 代码块（OCR 识别出的图中文字）
- 输出文件统一使用 UTF-8 编码

## 依赖安装 / Install dependencies

```bash
pip install -r requirements.txt        # pymupdf、Pillow、pytesseract
```

tesseract 引擎（非 pip 包，需含 chi_sim 与 eng 语言包）：
- Windows：https://github.com/UB-Mannheim/tesseract 安装时勾选简体中文语言包
- macOS：`brew install tesseract tesseract-lang`
- Linux：`sudo apt install tesseract-ocr tesseract-ocr-chi-sim`

## 降级方案 / Fallback（脚本不可用时）

若 Python 环境缺少依赖且无法安装：
1. 向用户说明需要安装 pymupdf 等依赖后重试；或
2. 使用 opencode 自带的解析（parse）工具先提取 PDF 文本内容交付用户，并说明完整转换（含图片提取与 OCR）需要依赖就绪。
If dependencies cannot be installed, tell the user and fall back to extracting PDF text with the built-in parse tool.

## 常见问题 / Troubleshooting

| 现象 / Issue | 处理 / Fix |
|------|------|
| 缺少 pymupdf / pymupdf missing | `pip install pymupdf` |
| 未找到 tesseract，OCR 被跳过 / tesseract not found | 设置环境变量 `TESSERACT_PATH` 指向 tesseract 可执行文件；确认 tessdata 含 `chi_sim.traineddata` 与 `eng.traineddata` |
| OCR 识别不出中文 / Chinese not recognized | 确认已安装简体中文语言包；脚本内置放大 3 倍与对比度增强预处理 |
| 识别结果含大量噪声 / noisy OCR output | 自动过滤装饰符行、去除中文间多余空格；仍不理想可检查原图清晰度 |