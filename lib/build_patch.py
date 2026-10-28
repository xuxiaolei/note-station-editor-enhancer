#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
给 Synology Note Station Client 打补丁（只构建，不安装）

做三件事：
  1. 把 patch/syno_markdown、patch/syno_beautify 两个 TinyMCE 插件放进 app.asar
  2. 往 content_css 与 skin 的 content.min.css 追加统一表格样式（幂等）
  3. 改 notestation.js 三处：plugins 列表 2 处 + 工具栏分组 1 处（幂等、兼容旧补丁）

用法:
    python3 build_patch.py <srcdir> <out_asar> [base_asar]

退出码:
    0  成功
    2  锚点不匹配（该 App 版本未适配），此时不会修改任何文件
"""
import os
import shutil
import sys

import asar_tool

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # 套件根目录
APP = '/Applications/Synology Note Station Client.app'
DEFAULT_BASE = os.path.join(APP, 'Contents/Resources/app.asar')

PLUGIN_SRCS = [
    ('patch/syno_markdown', 'build/webman/modules/TinyMCE/js/tinymce/plugins/syno_markdown'),
    ('patch/syno_beautify', 'build/webman/modules/TinyMCE/js/tinymce/plugins/syno_beautify'),
]
CONTENT_CSS_SRC = os.path.join(ROOT, 'patch/content_css/note_content_patch.css')
# notestation.js 的 content_css 指向 3rdparty/NoteStation/js/tinymce_plugins/note_content_patch.css，
# 而该目录是 asar 内软链 -> modules/TinyMCE/js/tinymce/plugins，真实文件是下面这个
CONTENT_CSS_REL = 'build/webman/modules/TinyMCE/js/tinymce/plugins/note_content_patch.css'
CONTENT_CSS_MARK = '/* syno_markdown: unified table style */'
# 保险：skin 的 content.min.css 是编辑器 iframe 必加载的文件（实测 content_css 那条链路不生效）
SKIN_CSS_REL = 'build/webman/modules/TinyMCE/js/tinymce/skins/synostyle/content.min.css'
SKIN_CSS_MARK = '/*syno_markdown:table*/'

# ---- notestation.js 锚点（多版本兼容）----
# plugins 串在文件里出现 2 次：主编辑器 fillConfig + initTinymcePlugins 预加载
PLUGIN_FINAL = '"syno_autolink syno_searchreplace syno_markdown syno_beautify hr syno_table"'
PLUGIN_VARIANTS = [
    '"syno_autolink syno_searchreplace hr syno_table"',                        # 原版
    '"syno_autolink syno_searchreplace syno_markdown hr syno_table"',          # 只装过 markdown
]

TOOLBAR_FINAL = '["undo","redo","syno_markdown","syno_beautify"]'
# getTinyMCEToolbarConfig 的第一个分组就是 ["undo","redo"]（全文唯一）
# 放在最左侧分组，避免被工具栏右侧「»」折叠菜单吞掉（放末尾实测会进折叠区）
TOOLBAR_ANCHOR = ['["undo","redo"]']
# 旧版补丁把按钮追加在末尾，若基线里存在先还原，避免出现重复按钮
TOOLBAR_OLD_TAIL = [
    '["syno_image","syno_recorder","syno_formupload","syno_search","syno_markdown","syno_beautify"]',
    '["syno_image","syno_recorder","syno_formupload","syno_search","syno_markdown"]',
]
TOOLBAR_TAIL_ORIG = '["syno_image","syno_recorder","syno_formupload","syno_search"]'


def patch_once(s, variants, final, expect):
    """把 variants 中的任一版本替换成 final，并校验替换前后总量等于 expect。"""
    total = s.count(final) + sum(s.count(v) for v in variants)
    if total != expect:
        raise SystemExit(
            f'锚点数量不符（期望 {expect}，实际 {total}）：{final[:60]}…\n'
            '该 App 版本结构与本补丁不匹配，已中止，未修改任何文件。'
        )
    for v in variants:
        if v in s:
            s = s.replace(v, final)
    return s


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    srcdir, out = sys.argv[1], sys.argv[2]
    base = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_BASE

    notestation = os.path.join(srcdir, 'build/webman/3rdparty/NoteStation/notestation.js')
    if not os.path.isfile(notestation):
        raise SystemExit('srcdir 不对，找不到 ' + notestation)

    # 1. 放置插件
    for src_rel, dst_rel in PLUGIN_SRCS:
        src = os.path.join(ROOT, src_rel)
        dst = os.path.join(srcdir, dst_rel)
        if not os.path.isdir(src):
            raise SystemExit('缺少插件源目录: ' + src)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copytree(src, dst)
    print('  [1/5] 插件已放入: ' + ', '.join(os.path.basename(d) for _, d in PLUGIN_SRCS))

    # 1b. 追加表格统一样式（幂等）：content_css + skin 双保险
    if not os.path.isfile(CONTENT_CSS_SRC):
        raise SystemExit('缺少 content_css 源片段: ' + CONTENT_CSS_SRC)
    with open(CONTENT_CSS_SRC, encoding='utf-8') as f:
        snippet = f.read()

    def append_once(rel, mark):
        path = os.path.join(srcdir, rel)
        if not os.path.isfile(path):
            raise SystemExit('找不到样式文件: ' + path)
        with open(path, encoding='utf-8') as f:
            cur = f.read()
        if mark in cur:
            return False
        with open(path, 'w', encoding='utf-8') as f:
            f.write(cur.rstrip() + '\n\n' + mark + '\n' + snippet)
        return True

    done = []
    if append_once(CONTENT_CSS_REL, CONTENT_CSS_MARK):
        done.append('content_css')
    if append_once(SKIN_CSS_REL, SKIN_CSS_MARK):
        done.append('skin')
    print('  [2/5] 表格样式' + ('已追加: ' + ' + '.join(done) if done else '已存在，跳过'))

    # 2. notestation.js 补丁（幂等 + 兼容旧版补丁状态）
    with open(notestation, encoding='utf-8') as f:
        s = f.read()
    before = s
    s = patch_once(s, PLUGIN_VARIANTS, PLUGIN_FINAL, 2)
    for old in TOOLBAR_OLD_TAIL:
        if old in s:
            s = s.replace(old, TOOLBAR_TAIL_ORIG)
    s = patch_once(s, TOOLBAR_ANCHOR, TOOLBAR_FINAL, 1)
    if s != before:
        with open(notestation, 'w', encoding='utf-8') as f:
            f.write(s)
        print('  [3/5] notestation.js 已打补丁：plugins 2 处 + toolbar 1 处')
    else:
        print('  [3/5] notestation.js 已是补丁状态，跳过')

    # 3. 重打包
    size = asar_tool.pack(out, srcdir, base)
    print(f'  [4/5] 已重打包: {os.path.basename(out)}  size={size}')

    # 4. 自检
    checked, bad = asar_tool.verify(out, srcdir)
    print(f'  [5/5] 自检: 文件数 {checked}, 异常 {len(bad)}')
    if bad:
        for b in bad[:5]:
            print('     ', b)
        raise SystemExit('自检失败，已中止')


if __name__ == '__main__':
    sys.path.insert(0, HERE)
    main()
