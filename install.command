#!/bin/sh
# Synology Note Station Client —— Markdown / 一键美化 补丁套件
#
#   ./install.command            安装（会弹管理员授权）
#   ./install.command --check    只检查兼容性，不改任何文件
#   ./install.command --restore  还原原始版本
#   ./install.command --root     内部使用（已提权）
set -u
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP 2>/dev/null || true
PYTHONNOUSERSITE=1
export PYTHONNOUSERSITE

KIT=$(cd "$(dirname "$0")" && pwd)
APP="/Applications/Synology Note Station Client.app"
PY=/usr/bin/python3
PYFLAGS="-E -S"

ROOT=0
MODE=install
for a in "$@"; do
    case "$a" in
        --root)    ROOT=1 ;;
        --check)   MODE=check ;;
        --restore) MODE=restore ;;
        -h|--help) MODE=help ;;
    esac
done

if [ "$MODE" = "help" ]; then
    sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
fi

if [ ! -d "$APP" ]; then
    printf '未找到应用：%s\n请先把 Note Station 客户端装到 /Applications。\n' "$APP"
    exit 1
fi
if [ ! -x "$PY" ]; then
    printf '缺少 python3。请先安装命令行工具：xcode-select --install\n'
    exit 1
fi

if [ "$MODE" = "check" ]; then
    "$PY" $PYFLAGS "$KIT/lib/selfcheck.py" "$APP"
    exit $?
fi

# 修改 /Applications 下的应用包需要管理员权限
if [ "$ROOT" = "0" ]; then
    FLAG=""
    [ "$MODE" = "restore" ] && FLAG="--restore"
    case "$KIT" in
        *\"*|*\'*) printf '套件路径包含引号，无法自动提权，请手动执行：\n  sudo /bin/sh "%s/lib/apply_root.sh" "%s" %s\n' "$KIT" "$KIT" "$MODE"; exit 1 ;;
    esac
    printf '需要管理员权限（要改写 /Applications 下的应用包）…\n'
    osascript -e "do shell script \"/bin/sh '$KIT/install.command' --root $FLAG\" with administrator privileges" || {
        printf '已取消，未做任何修改。\n'
        exit 1
    }
    printf '\n== 重新启动应用\n'
    open -a "$APP" 2>/dev/null || true
    exit 0
fi

/bin/sh "$KIT/lib/apply_root.sh" "$KIT" "$MODE"
