#!/bin/bash
# Mermaid 插件回归测试（需要 Chrome）
# 用最小 stub 模拟 Note Station 页面里的 Prototype.js（Array.prototype.each），
# 验证插件产出的 SVG 仍是合法 XML、data URI 图片不会裂图。
set -u

DIR="$(cd "$(dirname "$0")" && pwd)"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PAGE="file://$DIR/test_mermaid.html"

if [ ! -x "$CHROME" ]; then
  echo "SKIP: 未找到 Chrome"
  exit 0
fi

OUT=$("$CHROME" --headless=new --disable-gpu --no-sandbox --virtual-time-budget=30000 \
      --dump-dom "$PAGE" 2>/dev/null \
      | python3 -c "
import sys, re, html
s = sys.stdin.read()
m = re.search(r'<pre id=\"out\">(.*?)</pre>', s, re.S)
print(html.unescape(m.group(1)) if m else 'NO OUTPUT')
t = re.search(r'<title>(.*?)</title>', s)
print('--- title: ' + (t.group(1) if t else '?'))
")

echo "$OUT"
if echo "$OUT" | grep -q "^ALL PASS"; then
  exit 0
fi
exit 1
