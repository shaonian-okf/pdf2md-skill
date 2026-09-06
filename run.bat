@echo off
chcp 65001 >nul
title pdf2md - PDF 转 Markdown 工具
echo ==================================================
echo   pdf2md - PDF 转完整 Markdown（含图片与OCR解析）
echo ==================================================
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

if "%~1"=="" (
    set /p PDF_FILE="请输入 PDF 文件路径（可直接拖入）："
) else (
    set "PDF_FILE=%~1"
)

if not exist "%PDF_FILE%" (
    echo [错误] 文件不存在: %PDF_FILE%
    pause
    exit /b 1
)

python "pdf2md\scripts\pdf2md.py" "%PDF_FILE%"

echo.
pause