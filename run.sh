#!/usr/bin/env bash
# pdf2md — PDF 转 Markdown 工具（Linux / macOS 启动器）
# PDF → Markdown launcher for Linux / macOS (Windows users: use run.bat)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

if [ -n "$1" ]; then
    PDF_FILE="$1"
    shift
else
    printf '请输入 PDF 文件路径（可直接拖入）：'
    read -r PDF_FILE
fi

if [ ! -f "$PDF_FILE" ]; then
    echo "[错误] 文件不存在: $PDF_FILE"
    exit 1
fi

# 优先 python3；若不存在则回退到 python
PY=python3
if ! command -v python3 >/dev/null 2>&1; then
    PY=python
fi

exec "$PY" .opencode/skills/pdf2md/scripts/pdf2md.py "$PDF_FILE" "$@"