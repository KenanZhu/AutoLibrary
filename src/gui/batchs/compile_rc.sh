#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PARENT_DIR"

echo "[AutoLibrary compile] 检查翻译文件..."
if [ -d "translators" ]; then
    cd translators
    ts_files=(*.ts)
    ts_count=${#ts_files[@]}

    # 如果第一个元素是"*.ts"（表示没有匹配），则数量为0
    if [ "$ts_count" -eq 1 ] && [ "${ts_files[0]}" = "*.ts" ]; then
        ts_count=0
    fi

    if [ $ts_count -gt 0 ]; then
        echo "[AutoLibrary compile] 找到 $ts_count 个 .ts 文件，开始编译翻译文件..."
        for file in *.ts; do
            base_name=$(basename "$file" .ts)
            qm_file="${base_name}.qm"
            echo "[AutoLibrary compile] 正在编译翻译文件: \"$file\" -> \"$qm_file\""

            if pyside6-lrelease "$file"; then
                echo "[AutoLibrary compile] 翻译文件 \"$file\" ✓ 编译成功，输出文件: \"$qm_file\""
            else
                echo "[AutoLibrary compile] 翻译文件 \"$file\" ✗ 编译失败"
            fi
        done
        echo
    else
        echo "[AutoLibrary compile] 未找到任何 .ts 翻译文件"
    fi
    cd ..
else
    echo "[AutoLibrary compile] 未找到 translators 目录"
fi
echo

file_count=$(ls *.qrc 2>/dev/null | wc -l)

if [ $file_count -eq 0 ]; then
    echo "[AutoLibrary compile] 错误: 未找到任何 .qrc 文件"
    exit 1
fi

echo "[AutoLibrary compile] 找到 $file_count 个 .qrc 文件，开始编译..."
echo

for file in *.qrc; do
    base_name=$(basename "$file" .qrc)
    output_file="${base_name}.py"
    echo "[AutoLibrary compile] 正在编译: \"$file\" -> \"$output_file\""

    if pyside6-rcc "$file" -o "$output_file"; then
        echo "[AutoLibrary compile] 文件 \"$file\" ✓ 编译成功，输出文件: \"$output_file\""
    else
        echo "[AutoLibrary compile] 文件 \"$file\" ✗ 编译失败"
    fi
    echo
done

echo "[AutoLibrary compile] 所有操作完成。"