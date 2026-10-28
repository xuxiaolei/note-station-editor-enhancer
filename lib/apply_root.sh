#!/bin/sh
# 以 root 身份执行安装 / 还原（由 install.command 提权后调用）
# 用法: apply_root.sh <套件目录> <install|restore>
set -eu
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP 2>/dev/null || true
PYTHONNOUSERSITE=1
export PYTHONNOUSERSITE
PATH=/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin

KIT="$1"
MODE="${2:-install}"
APP="/Applications/Synology Note Station Client.app"
ASAR="$APP/Contents/Resources/app.asar"
PY=/usr/bin/python3
# -E 忽略 PYTHON* 环境变量；-S 不加载 sitecustomize（某些环境会注入文件访问代理/沙箱钩子）
PYFLAGS="-E -S"
BACKUP_DIR="$KIT/backup"

say() { printf '%s\n' "$*"; }
die() { printf '错误: %s\n' "$*" >&2; exit 1; }

[ -d "$APP" ] || die "未找到应用：$APP"
[ -x "$PY" ] || die "需要 python3（可执行 xcode-select --install 安装命令行工具）"

VERSION=$(/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" "$APP/Contents/Info.plist" 2>/dev/null || echo unknown)
ORIG="$BACKUP_DIR/app.asar.$VERSION.orig.bak"
mkdir -p "$BACKUP_DIR"
say "== 目标应用 : $APP"
say "== 版本     : $VERSION"

# 关掉正在运行的实例，避免文件被占用 / 补丁后仍用旧进程
# 只按进程名精确匹配：pkill -f 会连包含该字符串的 shell 自身一起杀掉
pkill -x "Synology Note Station Client" 2>/dev/null || true
sleep 2

if [ "$MODE" = "restore" ]; then
    B="$ORIG"
    if [ ! -f "$B" ]; then
        B=$(ls -1t "$BACKUP_DIR"/app.asar.*.orig.bak 2>/dev/null | head -1 || true)
    fi
    [ -n "${B:-}" ] || die "没有找到原始备份（$BACKUP_DIR），无法还原"
    say "== 还原自   : $(basename "$B")"
    cp "$B" "$ASAR"
else
    # 1) 兼容性检查（不通过就完全不改文件）
    set +e
    "$PY" $PYFLAGS "$KIT/lib/selfcheck.py" "$APP"
    CODE=$?
    set -e
    [ "$CODE" = "1" ] && die "版本不兼容，已中止（未修改任何文件）"

    # 2) 备份 / 选基线
    BASE="$ASAR"
    if [ "$CODE" = "0" ]; then
        if [ ! -f "$ORIG" ]; then
            say "== 备份原始 : $(basename "$ORIG")"
            cp "$ASAR" "$ORIG"
        else
            say "== 已存在原始备份，跳过备份"
        fi
    elif [ -f "$ORIG" ]; then
        # 已是补丁版，但有干净基线：从基线重打，避免补丁层层叠加
        BASE="$ORIG"
        say "== 当前已打补丁，改用原始备份作为基线: $(basename "$ORIG")"
    else
        say "== 注意: 当前已是补丁版且无原始备份，将以现状为基线重打"
        cp "$ASAR" "$BACKUP_DIR/app.asar.$VERSION.patched.bak"
    fi

    # 3) 解包 -> 打补丁 -> 重打包 -> 自检（全程在临时目录，失败不影响应用）
    TMP=$(mktemp -d /tmp/ns-kit.XXXXXX)
    trap 'rm -rf "$TMP"' EXIT INT TERM
    say "== 解包 $(basename "$BASE") ..."
    "$PY" $PYFLAGS "$KIT/lib/asar_tool.py" unpack "$BASE" "$TMP/x" >/dev/null
    say "== 打补丁 ..."
    "$PY" $PYFLAGS "$KIT/lib/build_patch.py" "$TMP/x" "$TMP/patched.bin" "$BASE"

    # 4) 替换（签名随后统一重做）
    say "== 写入应用并重签名 ..."
    cp "$TMP/patched.bin" "$ASAR"
fi

# 改过 asar 后 Developer ID 签名必然失效，重新做 adhoc 签名
codesign --force --deep --sign - "$APP" >/dev/null 2>&1 || die "重签名失败"
xattr -dr com.apple.quarantine "$APP" 2>/dev/null || true

# 备份目录归还给当前登录用户，避免之后手动操作遇到权限问题
OWNER=$(stat -f %Su /dev/console 2>/dev/null || echo "")
if [ -n "$OWNER" ] && [ "$OWNER" != "root" ]; then
    chown -R "$OWNER" "$BACKUP_DIR" 2>/dev/null || true
fi

say "== 签名     : $(codesign -dv "$APP" 2>&1 | grep -m1 'Signature=' || echo unknown)"
say "== 完成     : 请重新打开应用"
[ "$MODE" = "install" ] && say "   （重签名后首次启动可能弹钥匙串授权，输入登录密码并选“始终允许”）"
exit 0
