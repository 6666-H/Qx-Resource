#!/bin/bash
set -e

# 所有要合并的 URL，只改这里即可
URLS=(
  "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/rewrite.snippet"
  "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/weibo.snippet"
)

OUTPUT="Rewrite/Ad/Ad_merge.snippet"

# 下载并清理
i=1
for url in "${URLS[@]}"; do
  curl -sSL "$url" -o "tmp${i}.snippet"

  # 只保留规则行，去掉注释和源码
  grep -vE '^\s*#' "tmp${i}.snippet" | \
  grep -E '^(hostname|^https?:\/\/|^url-|.*reject.*|.*script-)' > "tmp${i}.clean"

  i=$((i+1))
done

# 合并 hostname
HOSTS=$(grep -hi '^hostname' tmp*.clean \
    | sed 's/hostname *=//I' \
    | tr ',' '\n' \
    | tr -d ' ' \
    | sort -u \
    | paste -sd, - )

# 去掉原 hostname 行
for f in tmp*.clean; do
  grep -vi '^hostname' "$f" > "${f%.clean}.nohost"
done

# 输出结果并去掉空行
{
  echo "# 奶思去广告合集 (QuantumultX 重写规则合并)"
  echo "# 自动生成：仅保留规则（去掉注释 & 去掉源码）"
  echo "# 更新时间: $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""
  [ -n "$HOSTS" ] && echo "hostname = $HOSTS"
  echo ""
  cat tmp*.nohost
} | awk 'NF' > "$OUTPUT"

# 清理
rm tmp*.snippet tmp*.clean tmp*.nohost
