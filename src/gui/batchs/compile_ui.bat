@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cd /d "%~dp0.."

set count=0
for %%f in (*.ui) do set /a count+=1

if %count% equ 0 (
    echo [AutoLibrary compile] 错误: 未找到任何 .ui 文件
    pause
    exit /b 1
)

echo [AutoLibrary compile] 找到 %count% 个 .ui 文件，开始编译...
echo.

for %%f in (*.ui) do (
    set "filename=%%~nf"
    set "output_file=Ui_!filename!.py"
    echo [AutoLibrary compile] 正在编译: "%%f" -> "!output_file!"

    pyside6-uic "%%f" -o "!output_file!"
    if !errorlevel! equ 0 (
        echo [AutoLibrary compile] 文件 "%%f" ✓ 编译成功，输出文件: "!output_file!"
    ) else (
        echo [AutoLibrary compile] 文件 "%%f" ✗ 编译失败
    )
    echo.
)

echo [AutoLibrary compile] 所有操作完成。