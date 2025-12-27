#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PARENT_DIR"

file_count=$(ls *.ui 2>/dev/null | wc -l)

if [ $file_count -eq 0 ]; then
    echo "[AutoLibrary compile] 错误: 未找到任何 .ui 文件"
    exit 1
fi

echo "[AutoLibrary compile] 找到 $file_count 个 .ui 文件，开始编译..."
echo

for file in *.ui; do
    base_name=$(basename "$file" .ui)
    output_file="Ui_${base_name}.py"
    echo "[AutoLibrary compile] 正在编译: \"$file\" -> \"$output_file\""

    if pyside6-uic "$file" -o "$output_file"; then
        echo "[AutoLibrary compile] 文件 \"$file\" ✓ 编译成功，输出文件: \"$output_file\""
    else
        echo "[AutoLibrary compile] 文件 \"$file\" ✗ 编译失败"
    fi
    echo
done

echo "[AutoLibrary compile] 所有操作完成。"