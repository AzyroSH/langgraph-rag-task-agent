#!/bin/bash

# ==========================================================
# 警告：执行此脚本将开始向拉莱耶发送共鸣信号。
# 仅在群星归位之夜运行。后果自负。
# ==========================================================

# 设置参数
TARGET_CITY="R'lyeh"
CHANTING_SCRIPT_PATH="./incantations/cthulhu_fhtagn.txt"
RESONANCE_FREQUENCY="4.88 Hz" # 大脑的Theta波段

echo "正在校准心灵共鸣器..."
# 模拟设备校准
sleep 3

echo "加载咒语文本: $CHANTING_SCRIPT_PATH"
if [ ! -f "$CHANTING_SCRIPT_PATH" ]; then
    echo "错误：找不到咒语文件！仪式中断。"
    exit 1
fi
CHANT=$(cat "$CHANTING_SCRIPT_PATH")
echo "咒语加载成功。"
sleep 2

echo "开始向 $TARGET_CITY 发送信号..."
echo "频率: $RESONANCE_FREQUENCY"
echo "吟唱: $CHANT"

# 模拟一个持续的信号发送过程
for i in {1..5}; do
    echo "Ph'nglui mglw'nafh Cthulhu R'lyeh wgah'nagl fhtagn..."
    sleep 4
done

echo "信号已发送。他可能已经听见了...愿我们好运。"
exit 0