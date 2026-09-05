# pdf2md 技能安装手册 / Installation Manual

本手册指导你从零开始安装 pdf2md 技能的全部依赖，适用于 Windows、Linux、macOS。
This manual guides you through installing all dependencies of the pdf2md skill on Windows, Linux and macOS.

> **快捷方式 / Quick start**：一条命令完成 Python 依赖与语言包的检查/安装：
> `python .opencode/skills/pdf2md/scripts/install_deps.py`

---

## 中文版 / Chinese

### 一、系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10+ / Linux / macOS |
| Python | 3.7 及以上（安装时勾选"加入 PATH"） |
| 磁盘空间 | 约 300 MB（含 tesseract 引擎与语言包） |
| 网络 | 安装阶段需要联网（已有依赖时可离线，见"离线安装"） |

### 二、一键安装（推荐）

在项目根目录执行：

```bash
python .opencode/skills/pdf2md/scripts/install_deps.py
```

脚本会自动完成：
1. 通过 pip 安装 Python 依赖：pymupdf、Pillow、pytesseract（见 requirements.txt）
2. 检测 tesseract 引擎；未找到时按你的系统给出安装指引
3. 检测简体中文（chi_sim）与英文（eng）语言包；缺失时自动下载到技能目录 `tessdata/`

> 若只想执行其中一部分，可用参数：`--skip-pip` 跳过依赖安装；`--skip-tessdata` 跳过语言包下载。

### 三、手动安装（分步）

#### 1. 安装 Python 依赖

**在线安装：**
```bash
pip install -r requirements.txt
```

**离线安装（无网络环境）：**
先在有网络的机器上准备离线包：
```bash
pip download -r requirements.txt -d packages/
```
再将 `packages/` 目录随项目一同拷贝到目标机器，然后：
```bash
pip install --no-index --find-links=packages/ -r requirements.txt
```

#### 2. 安装 Tesseract OCR 引擎

| 系统 | 安装方式 |
|------|----------|
| Windows | 下载 https://github.com/UB-Mannheim/tesseract 安装包，**安装时勾选简体中文语言包**；或解压绿色版并设置环境变量 `TESSERACT_PATH` |
| macOS | `brew install tesseract tesseract-lang` |
| Linux | Debian/Ubuntu：`sudo apt install tesseract-ocr tesseract-ocr-chi-sim`；Fedora：`sudo dnf install tesseract tesseract-langpack-chi_sim` |

#### 3. 准备语言包（chi_sim / eng）

- **自动方式**：运行一键安装脚本，缺失的 `chi_sim.traineddata` 与 `eng.traineddata` 会自动下载到技能目录 `tessdata/`。
- **手动方式**：从 https://github.com/tesseract-ocr/tessdata 下载这两个文件，放入技能目录下的 `tessdata/` 文件夹。

> 语言包存放位置：`.opencode/skills/pdf2md/tessdata/`（脚本启动时会自动搜索该目录）。

#### 4. 设置环境变量（可选但推荐）

将 `TESSERACT_PATH` 指向 tesseract 可执行文件：

```powershell
# Windows PowerShell
setx TESSERACT_PATH "C:\Program Files\Tesseract-OCR\tesseract.exe"
```
```bash
# Linux / macOS
export TESSERACT_PATH=/usr/bin/tesseract
# 写入 ~/.bashrc 或 ~/.zshrc 使其永久生效
```

### 四、验证安装

运行一次真实转换测试：

```bash
python .opencode/skills/pdf2md/scripts/pdf2md.py some.pdf output_folder
```

- 看到 `[工具] 使用 tesseract: ...` 且输出"OCR 识别图片数量"大于 0，说明全套就绪。
- 若提示"未找到 tesseract.exe"，仅文本与图片导出可用，OCR 被跳过——请检查第三步。

### 五、离线安装（完全无网络）

1. 在有网的机器上执行 `pip download -r requirements.txt -d packages/`，连同 tesseract 安装包、`chi_sim.traineddata`、`eng.traineddata` 一并拷贝到目标机器。
2. 离线安装 Python 依赖（见上文）。将语言包放入 `tessdata/`。
3. Windows 直接运行 tesseract 安装包；Linux 使用本机已有的包缓存（如离线 apt 仓库）。

### 六、常见问题

| 问题 | 解决 |
|------|------|
| 提示缺少 pymupdf | `pip install pymupdf` 或重跑安装脚本 |
| 未找到 tesseract | 按"三-2"安装，或设置 `TESSERACT_PATH` |
| OCR 识别不出中文 | 确认 `chi_sim.traineddata` 存在于 tessdata 目录 |
| 下载语言包超时 | 网络受限时改用手动下载，放入 `tessdata/` 后重试 |

---

## English Version

### Requirements

| Item | Requirement |
|------|-------------|
| OS | Windows 10+ / Linux / macOS |
| Python | 3.7+ (add to PATH during install) |
| Disk | ~300 MB (engine + language data) |
| Network | needed only during installation (offline is possible, see below) |

### One-click install (recommended)

Run from the project root:

```bash
python .opencode/skills/pdf2md/scripts/install_deps.py
```

The script will: ①install Python deps via pip (pymupdf, Pillow, pytesseract); ②detect the tesseract engine and print platform-specific guidance if missing; ③download missing `chi_sim`/`eng` language data into the skill's `tessdata/` folder.

Skip parts with `--skip-pip` or `--skip-tessdata`.

### Manual install

1. **Python deps** — online: `pip install -r requirements.txt`. Offline: `pip download -r requirements.txt -d packages/` on a networked machine, then `pip install --no-index --find-links=packages/ -r requirements.txt`.
2. **Tesseract engine** — Windows: [UB-Mannheim installer](https://github.com/UB-Mannheim/tesseract) (check the Simplified Chinese language pack). macOS: `brew install tesseract tesseract-lang`. Linux: `sudo apt install tesseract-ocr tesseract-ocr-chi-sim`.
3. **Language data** — auto: run the install script; manual: download `chi_sim.traineddata` and `eng.traineddata` from [tesseract-ocr/tessdata](https://github.com/tesseract-ocr/tessdata) into `.opencode/skills/pdf2md/tessdata/`.
4. **Environment variable (optional but recommended)** — set `TESSERACT_PATH` to the tesseract executable.

### Verify

```bash
python .opencode/skills/pdf2md/scripts/pdf2md.py some.pdf output_folder
```

If you see `[Tool] Using tesseract:` and an OCR image count greater than zero, everything works.

### Offline install

Prepare `packages/` (via `pip download`), the tesseract installer and the two `.traineddata` files on a networked machine, copy them over, offline-install the pip deps, place language data into `tessdata/`, and install tesseract from the local package.

### FAQ

| Issue | Fix |
|-------|-----|
| pymupdf missing | `pip install pymupdf` or re-run the install script |
| tesseract not found | install per manual step 2, or set `TESSERACT_PATH` |
| Chinese OCR not working | make sure `chi_sim.traineddata` exists in the tessdata folder |
| language download timeout | download manually and put the files into `tessdata/` |