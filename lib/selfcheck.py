#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
只读兼容性检查：判断当前安装的 Note Station 能否安全打补丁。

用法:
    python3 selfcheck.py "/Applications/Synology Note Station Client.app"

退出码:
    0  原版，可打补丁
    2  已经打过补丁
    1  版本不兼容或文件异常（不要继续）
"""
import os
import plistlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asar_tool

APP = '/Applications/Synology Note Station Client.app'

PLUGIN_ANCHOR_ORIG = '"syno_autolink syno_searchreplace hr syno_table"'
PLUGIN_ANCHOR_MID = '"syno_autolink syno_searchreplace syno_markdown hr syno_table"'
PLUGIN_ANCHOR_NEW = '"syno_autolink syno_searchreplace syno_markdown syno_beautify hr syno_table"'
TOOLBAR_ANCHOR_ORIG = '["undo","redo"]'
TOOLBAR_NEW = '["undo","redo","syno_markdown","syno_beautify"]'
NS_REL = '/build/webman/3rdparty/NoteStation/notestation.js'


def read_bundle_info(app):
    info = os.path.join(app, 'Contents/Info.plist')
    if not os.path.isfile(info):
        return {}
    with open(info, 'rb') as f:
        return plistlib.load(f)


def main():
    app = sys.argv[1] if len(sys.argv) > 1 else APP
    app = app.rstrip('/')
    if app.endswith('app.asar'):
        app = os.path.dirname(os.path.dirname(os.path.dirname(app)))
    asar = os.path.join(app, 'Contents/Resources/app.asar')

    print('应用路径 :', app)
    if not os.path.isdir(app):
        print('结论     : ✗ 未找到应用')
        return 1

    info = read_bundle_info(app)
    print('版本     :', info.get('CFBundleShortVersionString', '(未知)'),
          '(', info.get('CFBundleVersion', '-'), ')')

    if not os.path.isfile(asar):
        print('结论     : ✗ 找不到 app.asar')
        return 1
    print('app.asar :', asar, f'({os.path.getsize(asar) / 1048576:.1f} MB)')

    if 'ElectronAsarIntegrity' in info:
        print('提示     : Info.plist 记录了 asar 哈希（Electron 仅在开启校验开关时生效，'
              '本套件已在 3.0.0 上验证可正常启动）')

    try:
        header, base = asar_tool._read_header(asar)
        entries = dict(asar_tool._walk(header))
    except Exception as exc:                                    # noqa: BLE001
        print('结论     : ✗ asar 头部解析失败:', exc)
        return 1
    print('文件条目 :', len(entries))

    if NS_REL not in entries:
        print('结论     : ✗ 包里没有 notestation.js，布局不符')
        return 1

    meta = entries[NS_REL]
    with open(asar, 'rb') as f:
        f.seek(base + int(meta['offset']))
        js = f.read(int(meta['size'])).decode('utf-8', 'replace')

    n_new = js.count(PLUGIN_ANCHOR_NEW)
    n_mid = js.count(PLUGIN_ANCHOR_MID)
    n_orig = js.count(PLUGIN_ANCHOR_ORIG)
    t_new = js.count(TOOLBAR_NEW)
    t_orig = js.count(TOOLBAR_ANCHOR_ORIG)
    has_plugin = any('plugins/syno_markdown/plugin.min.js' in k for k in entries)

    print('锚点     : plugins 原版 %d / markdown %d / 全量 %d ；toolbar 原版 %d / 新版 %d'
          % (n_orig, n_mid, n_new, t_orig, t_new))
    print('插件     :', '已存在' if has_plugin else '未安装')

    if n_new == 2 and t_new == 1 and has_plugin:
        print('结论     : ✓ 已打过补丁（重跑安装会覆盖刷新）')
        return 2
    if n_orig + n_mid == 2 and t_orig >= 1:
        print('结论     : ✓ 原版结构，可以打补丁')
        return 0

    print('结论     : ✗ 锚点不匹配，该版本未适配，请勿继续')
    return 1


if __name__ == '__main__':
    sys.exit(main())
