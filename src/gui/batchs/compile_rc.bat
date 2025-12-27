@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cd /d "%~dp0.."

echo [AutoLibrary compile] 检查翻译文件...
if exist translators (
    cd translators
    set ts_count=0
    for %%f in (*.ts) do set /a ts_count+=1

    if !ts_count! gtr 0 (
        echo [AutoLibrary compile] 找到 !ts_count! 个 .ts 文件，开始编译翻译文件...
        for %%f in (*.ts) do (
            set "qm_filename=%%~nf.qm"
            echo [AutoLibrary compile] 正在编译翻译文件: "%%f" -> "!qm_filename!"

            pyside6-lrelease "%%f"
            if !errorlevel! equ 0 (
                echo [AutoLibrary compile] 翻译文件 "%%f" ✓ 编译成功，输出文件: "!qm_filename!"
            ) else (
                echo [AutoLibrary compile] 翻译文件 "%%f" ✗ 编译失败
            )
        )
        echo.
    ) else (
        echo [AutoLibrary compile] 未找到任何 .ts 翻译文件
    )
    cd ..
) else (
    echo [AutoLibrary compile] 未找到 translators 目录
)
echo.

set count=0
for %%f in (*.qrc) do set /a count+=1

if %count% equ 0 (
    echo [AutoLibrary compile] 错误: 未找到任何 .qrc 文件
    pause
    exit /b 1
)

echo [AutoLibrary compile] 找到 %count% 个 .qrc 文件，开始编译...
echo.

for %%f in (*.qrc) do (
    set "filename=%%~nf"
    set "output_file=!filename!.py"
    echo [AutoLibrary compile] 正在编译: "%%f" -> "!output_file!"

    pyside6-rcc "%%f" -o "!output_file!"
    if !errorlevel! equ 0 (
        echo [AutoLibrary compile] 文件 "%%f" ✓ 编译成功，输出文件: "!output_file!"
    ) else (
        echo [AutoLibrary compile] 文件 "%%f" ✗ 编译失败
    )
    echo.
)

echo [AutoLibrary compile] 所有操作完成。