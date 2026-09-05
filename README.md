# pdf2md — opencode 技能：PDF 转完整 Markdown

跨平台（Windows / Linux / macOS）的开源 [opencode](https://opencode.ai) 技能（skill），一键将任意 PDF 转换为**完整 Markdown**：全部文本、全部内嵌图片（按版面位置还原）、图片内文字的 OCR（光学字符识别）解析。控制台提示与文档支持**中英双语**。

> A cross-platform (Windows / Linux / macOS) open-source opencode skill that converts any PDF into a complete Markdown file — full text, all embedded images in their original layout positions, and OCR-extracted text from images. Console messages and docs are **bilingual (Chinese / English)**.

## 功能特性 / Features

1. **全部文本内容**：按页面还原版面顺序提取正文 / All text, preserving layout order per page.
2. **全部内嵌图片**：提取每一张图片并按版面坐标插入对应章节 / All embedded images inserted at their layout positions.
3. **图片内容 OCR**：中英双语识别（简体中文 + 英文），以 `【图片内容解析】` 代码块附在图片下方 / Bilingual OCR (Simplified Chinese + English) shown under each image.
4. **跨平台 / Cross-platform**：Python 脚本通用；Windows 用 `run.bat`，Linux/macOS 用 `run.sh`。
5. **中英双语 / Bilingual UI**：`--lang zh|en|auto` 切换控制台语言，自动检测系统语言。

## 目录结构 / Layout

```
pdf2md_tool/
├── .opencode/
│   └── skills/
│       └── pdf2md/              # opencode 技能定义（自包含，可整体拷贝）
│           ├── SKILL.md         # 技能说明：触发条件、工作流程、输出规范
│           └── scripts/
│               └── pdf2md.py    # 核心转换脚本（也可独立命令行运行）
├── requirements.txt             # Python 依赖清单
├── run.bat                      # Windows 一键运行
├── run.sh                       # Linux / macOS 一键运行
├── LICENSE                      # MIT 许可证
├── README.md                    # 本说明 / This file
└── .gitignore
```

---

## 中文文档 / Chinese Documentation

### 一、作为 opencode 技能使用 / Use as an opencode skill

**方式 A：复制到项目（推荐）/ Copy into your project (recommended)**

```bash
git clone https://github.com/<你的用户名>/pdf2md_tool.git
copy /Y pdf2md_tool\.opencode 你的项目\.opencode   # Windows
# Linux / macOS:
cp -r pdf2md_tool/.opencode ./你的项目/
```

然后**重启 opencode**，会话中直接说：

- "把 `xx.pdf` 转成 Markdown"
- "提取这个 PDF 的全部文本和图片，生成完整版 md"
- "Convert this PDF to Markdown with all images and OCR"

**方式 B：通过配置文件注册外部路径 / Register via config**

在项目的 `opencode.json` 中加入 `skills.paths`：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "skills": {
    "paths": ["D:/path/to/pdf2md_tool/.opencode/skills"]
  }
}
```

保存后重启 opencode 生效。

**方式 C：全局安装 / Global install**

复制 `.opencode/skills/pdf2md` 到 `~/.config/opencode/skills/pdf2md/`，所有项目均可使用。

### 二、作为独立命令行工具使用 / Standalone CLI

```bash
# 基本用法（输出到 PDF 所在目录）
python .opencode/skills/pdf2md/scripts/pdf2md.py 文档.pdf

# 指定输出目录
python .opencode/skills/pdf2md/scripts/pdf2md.py 文档.pdf output_folder

# 英文控制台提示
python .opencode/skills/pdf2md/scripts/pdf2md.py 文档.pdf --lang en
```

Windows 可拖放 PDF 到 `run.bat`；Linux/macOS 使用 `./run.sh 文档.pdf`。

### 三、安装依赖 / Install dependencies

**1. Python 依赖**

```bash
pip install -r requirements.txt
```

包含 `pymupdf`（文本与图片提取）、`Pillow`（图片预处理）、`pytesseract`（OCR 封装）。

**2. Tesseract OCR 引擎（中英语言包）**

| 系统 | 安装方式 |
|------|----------|
| Windows | <https://github.com/UB-Mannheim/tesseract> 下载安装，勾选简体中文语言包 |
| macOS | `brew install tesseract tesseract-lang` |
| Linux | `sudo apt install tesseract-ocr tesseract-ocr-chi-sim` |

脚本自动按以下顺序查找 tesseract：

1. 环境变量 `TESSERACT_PATH`（推荐显式配置）
2. 系统 PATH
3. 常见安装路径（Windows：`C:\Program Files\Tesseract-OCR` 等；Linux：`/usr/bin`、`/usr/local/bin` 等）
4. 技能目录周边的 `tesseract-extracted/` 目录

> 找不到 tesseract 时，**文本与图片仍会正常导出**，仅跳过 OCR 解析环节。

### 四、中英语言支持说明 / Language support

| 场景 | 说明 |
|------|------|
| OCR 识别语言 | 固定中英双语（`chi_sim+eng`），可识别中英文混排图片 |
| 控制台提示 | `--lang zh`（中文）/ `--lang en`（English）/ `--lang auto`（自动检测，默认） |
| Markdown 头部 | "来源 / Source、页数 / Pages" 中英双语并列显示 |
| 产物文件名 | 始终为 `<文件名>_完整版.md`（含中文，Windows 与 Linux 均兼容） |

### 五、输出说明 / Output

```
<输入文件名>_完整版.md    # 完整 Markdown（正文 + 图片引用 + OCR 解析）
images/                    # 提取的全部图片（相对路径统一用 /，跨平台渲染一致）
    ├── page1_img1.png
    └── ...
```

每张图片下方附有 `**【图片内容解析】**` 代码块，内容为 OCR 识别出的图中文字。

### 六、常见问题 / FAQ

| 问题 / Issue | 解决 / Fix |
|------|------|
| 提示缺少 pymupdf | `pip install pymupdf` |
| 未找到 tesseract | 设置环境变量 `TESSERACT_PATH` 指向 tesseract 可执行文件 |
| OCR 识别不出中文 | 确认已安装简体中文语言包（chi_sim.traineddata） |
| opencode 中技能未生效 | 确认目录为 `.opencode/skills/pdf2md/SKILL.md` 并重启 opencode |
| 控制台中文乱码（Windows） | 使用 `run.bat`（含 UTF-8 代码页切换）或较新的 Windows 终端 |

### 七、技术原理 / How it works

- **文本提取**：pymupdf 直接读取 PDF 文本层（无需 OCR）。
- **图片提取**：pymupdf 读取页面内嵌图片对象，导出为 PNG/JPEG。
- **图片 OCR**：tesseract 引擎 + chi_sim/eng 双语言模型，识别前自动放大 3 倍、增强对比度，并过滤装饰噪声行。
- **版面还原**：按页内文本块与图片块的 Y 坐标排序，还原原始阅读顺序。

---

## English Documentation

### Installation as an opencode skill

**Option A — Clone and copy into your project (recommended)**

```bash
git clone https://github.com/<your-username>/pdf2md_tool.git
cp -r pdf2md_tool/.opencode ./your-project/
```

Restart opencode, then say e.g. *"Convert xx.pdf to Markdown"* or *"Extract text and images from this PDF and OCR the figures."*

**Option B — Register an external path in `opencode.json`**

```json
{
  "$schema": "https://opencode.ai/config.json",
  "skills": {
    "paths": ["/path/to/pdf2md_tool/.opencode/skills"]
  }
}
```

**Option C — Global install:** copy `.opencode/skills/pdf2md` to `~/.config/opencode/skills/pdf2md/`.

### Standalone CLI usage

```bash
# Default: output next to the PDF
python .opencode/skills/pdf2md/scripts/pdf2md.py document.pdf

# Custom output directory
python .opencode/skills/pdf2md/scripts/pdf2md.py document.pdf out_folder

# English console messages
python .opencode/skills/pdf2md/scripts/pdf2md.py document.pdf --lang en
```

Windows: drag the PDF onto `run.bat`. Linux/macOS: `./run.sh document.pdf`.

### Dependencies

```bash
pip install -r requirements.txt   # pymupdf, Pillow, pytesseract
```

Tesseract OCR engine with `chi_sim` (Simplified Chinese) and `eng` language packs:
- Windows: https://github.com/UB-Mannheim/tesseract (check the Chinese language pack)
- macOS: `brew install tesseract tesseract-lang`
- Linux: `sudo apt install tesseract-ocr tesseract-ocr-chi-sim`

Detection order: `TESSERACT_PATH` env var → system PATH → common install paths → bundled `tesseract-extracted/` folders. If tesseract is missing, text and images are still exported; only OCR is skipped.

### Language support

- OCR is always bilingual (`chi_sim+eng`).
- Console messages: `--lang zh` / `--lang en` / `--lang auto` (default, auto-detected).
- Markdown header shows Source/Pages bilingually.
- Image paths in Markdown always use `/` so rendering is identical on Windows and Linux.

### Output

```
<input-name>_完整版.md     # Full Markdown (text + images + OCR blocks)
images/                    # Extracted images
```

### FAQ

| Issue | Fix |
|-------|-----|
| pymupdf missing | `pip install pymupdf` |
| tesseract not found | Set `TESSERACT_PATH` to the tesseract executable |
| Chinese OCR not working | Install the Simplified Chinese language pack (`chi_sim.traineddata`) |
| Skill not active in opencode | Check the path is `.opencode/skills/pdf2md/SKILL.md` and restart opencode |

## License

[MIT](LICENSE) © pdf2md contributors

Issues and pull requests are welcome.