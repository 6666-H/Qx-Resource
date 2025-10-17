#!/bin/bash
set -e

URL1="https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/rewrite.snippet"
URL2="https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/weibo.snippet"
OUTPUT="Rewrite/Ad/Ad_merge.snippet"

# 下载
curl -sSL $URL1 -o tmp1.snippet
curl -sSL $URL2 -o tmp2.snippet

# 去掉注释
grep -vE '^\s*#' tmp1.snippet > tmp1.clean
grep -vE '^\s*#' tmp2.snippet > tmp2.clean

# 提取并合并 hostname
HOSTS=$( (grep -i '^hostname' tmp1.clean; grep -i '^hostname' tmp2.clean) \
    | sed 's/hostname *=//I' \
    | tr ',' '\n' \
    | tr -d ' ' \
    | sort -u \
    | paste -sd, - )

# 去掉原 hostname 行
grep -vi '^hostname' tmp1.clean > tmp1.nohost
grep -vi '^hostname' tmp2.clean > tmp2.nohost

# 输出结果
echo "# 合并文件 (自动生成，无注释，合并hostname)" > $OUTPUT
echo "# 更新时间: $(date '+%Y-%m-%d %H:%M:%S')" >> $OUTPUT
echo "" >> $OUTPUT
echo "hostname = $HOSTS" >> $OUTPUT
echo "" >> $OUTPUT
cat tmp1.nohost >> $OUTPUT
echo "" >> $OUTPUT
cat tmp2.nohost >> $OUTPUT

# 清理临时文件
rm tmp1.snippet tmp2.snippet tmp1.clean tmp2.clean tmp1.nohost tmp2.nohost
