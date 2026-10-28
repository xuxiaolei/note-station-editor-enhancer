#!/bin/sh
# 一键还原：把 app.asar 换回安装前的原始备份，并重签名
# 等价的完整写法： ./install.command --restore
DIR=$(cd "$(dirname "$0")" && pwd)
exec /bin/sh "$DIR/install.command" --restore
