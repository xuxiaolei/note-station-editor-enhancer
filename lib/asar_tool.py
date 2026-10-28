#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
asar 读写工具（用于给 Synology Note Station Client 3.0.0 打补丁）

原应用为 Electron 37 + asar 打包，asar 头部结构（实测）：
    offset 0  : uint32 = 4                      (size 字段自身的长度)
    offset 4  : uint32 = header_size            (= padding 后的 JSON 长度 + 8)
    offset 8  : uint32 = header_size - 4
    offset 12 : uint32 = json_len               (未 padding 的 JSON 字节数)
    offset 16 : JSON 字节 (json_len) + 0x00 填充到 4 字节对齐
    数据区起始 = 8 + header_size = 16 + padded_json_len
文件数据按 JSON 中的顺序紧密排列，无对齐填充（实测 offset%4 分布均匀）。

用法:
    python3 asar_tool.py list  <asar>
    python3 asar_tool.py unpack <asar> <outdir>
    python3 asar_tool.py pack  <out.asar> <srcdir> [--base <orig.asar>] [--replace path=newfile]...
    python3 asar_tool.py verify <asar> <srcdir>
"""
import hashlib
import json
import os
import struct
import sys

BLOCK = 4194304


def _read_header(path):
    with open(path, 'rb') as f:
        raw = f.read(16)
        if len(raw) < 16:
            raise ValueError('文件过小，不是合法的 asar')
        _, header_size, _f3, json_len = struct.unpack('<4I', raw)
        padded = (json_len + 3) // 4 * 4
        data = f.read(padded)
        header = json.loads(data[:json_len].decode('utf-8'))
    base = 8 + header_size
    return header, base


def _walk(header):
    """按 JSON 顺序返回 [(绝对路径, meta)]"""
    out = []

    def rec(node, prefix):
        for name, meta in node.get('files', {}).items():
            p = prefix + '/' + name
            if 'files' in meta:
                rec(meta, p)
            else:
                out.append((p, meta))

    rec(header, '')
    return out


def _integrity(data):
    blocks = []
    for i in range(0, len(data), BLOCK):
        blocks.append(hashlib.sha256(data[i:i + BLOCK]).hexdigest())
    if not blocks:
        blocks = [hashlib.sha256(b'').hexdigest()]
    return {
        'algorithm': 'SHA256',
        'hash': hashlib.sha256(data).hexdigest(),
        'blockSize': BLOCK,
        'blocks': blocks,
    }


def unpack(asar_path, outdir):
    header, base = _read_header(asar_path)
    n = 0
    with open(asar_path, 'rb') as f:
        for p, meta in _walk(header):
            dst = os.path.join(outdir, p.lstrip('/'))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if 'link' in meta:
                continue
            size = int(meta.get('size') or 0)
            if size == 0:
                open(dst, 'wb').close()
            else:
                f.seek(base + int(meta['offset']))
                with open(dst, 'wb') as o:
                    o.write(f.read(size))
            n += 1
    return n


def pack(out_path, srcdir, base_asar=None, replaces=None):
    """以 base_asar 的头部为模板重打包；replaces 为 {asar内绝对路径: 本地文件}"""
    replaces = dict(replaces or {})
    header, _ = _read_header(base_asar)
    entries = _walk(header)
    have = {p for p, _ in entries}

    def insert(apath):
        """把 asar 内路径挂进 header 树（父目录不存在则创建）"""
        parts = apath.strip('/').split('/')
        node = header
        for name in parts[:-1]:
            child = node['files'].get(name)
            if child is None:
                child = {'files': {}}
                node['files'][name] = child
            if 'files' not in child:
                raise ValueError('路径冲突（同名文件已存在）: ' + apath)
            node = child
        if parts[-1] in node['files'] and 'files' in node['files'][parts[-1]]:
            raise ValueError('路径冲突（同名目录已存在）: ' + apath)
        node['files'][parts[-1]] = {}

    # a) replaces 中 base 里不存在的新文件
    for apath in replaces:
        if apath not in have:
            insert(apath)
            have.add(apath)

    # b) srcdir 里存在、但 header 中没有的普通文件（新增插件等）
    for root, dirs, fnames in os.walk(srcdir):
        dirs[:] = [d for d in dirs if d != '.DS_Store']
        for fn in fnames:
            if fn == '.DS_Store':
                continue
            full = os.path.join(root, fn)
            if os.path.islink(full):
                continue
            rel = '/' + os.path.relpath(full, srcdir).replace(os.sep, '/')
            if rel in have:
                continue
            insert(rel)
            have.add(rel)

    # 重新遍历（含新增项），按 JSON 顺序写数据
    entries = _walk(header)
    offset = 0
    out = open(out_path, 'wb')
    out.write(b'\x00' * 16)  # 占位，最后回填头部

    blobs = []
    for p, meta in entries:
        if 'link' in meta:
            continue
        src = replaces.get(p) or os.path.join(srcdir, p.lstrip('/'))
        with open(src, 'rb') as f:
            data = f.read()
        meta['size'] = len(data)
        meta['offset'] = str(offset)
        meta['integrity'] = _integrity(data)
        blobs.append((offset, data))
        offset += len(data)

    json_bytes = json.dumps(header, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    padded = (len(json_bytes) + 3) // 4 * 4
    header_size = padded + 8
    head = struct.pack('<4I', 4, header_size, padded + 4, len(json_bytes))
    head += json_bytes + b'\x00' * (padded - len(json_bytes))

    out.seek(0)
    out.write(head)
    out.seek(8 + header_size)
    for off, data in blobs:
        out.write(data)
    out.truncate()
    out.close()
    return 8 + header_size + offset


def verify(asar_path, srcdir):
    header, base = _read_header(asar_path)
    bad = []
    n = 0
    in_header = set()
    with open(asar_path, 'rb') as f:
        for p, meta in _walk(header):
            in_header.add(p)
            if 'link' in meta:
                continue
            src = os.path.join(srcdir, p.lstrip('/'))
            size = int(meta.get('size') or 0)
            f.seek(base + int(meta['offset']))
            got = f.read(size)
            want = b''
            if os.path.exists(src):
                want = open(src, 'rb').read()
            if got != want:
                bad.append((p, len(want), len(got)))
            n += 1
    # 磁盘上有、包内没有 = 漏打包
    for root, dirs, fnames in os.walk(srcdir):
        dirs[:] = [d for d in dirs if d != '.DS_Store']
        for fn in fnames:
            if fn == '.DS_Store' or os.path.islink(os.path.join(root, fn)):
                continue
            rel = '/' + os.path.relpath(os.path.join(root, fn), srcdir).replace(os.sep, '/')
            if rel not in in_header:
                bad.append(('MISSING', rel, 0))
    return n, bad


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    if cmd == 'list':
        header, base = _read_header(sys.argv[2])
        for p, m in _walk(header):
            print(f"{int(m.get('size') or 0):>10}  {p}")
        return 0
    if cmd == 'unpack':
        print('files:', unpack(sys.argv[2], sys.argv[3]))
        return 0
    if cmd == 'verify':
        n, bad = verify(sys.argv[2], sys.argv[3])
        print(f'checked {n}, mismatched {len(bad)}')
        for b in bad[:10]:
            print('  ', b)
        return 0 if not bad else 1
    if cmd == 'pack':
        out_path, srcdir = sys.argv[2], sys.argv[3]
        base_asar, replaces = None, {}
        i = 4
        while i < len(sys.argv):
            if sys.argv[i] == '--base':
                base_asar = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == '--replace':
                apath, local = sys.argv[i + 1].split('=', 1)
                replaces[apath] = local
                i += 2
            else:
                raise SystemExit('未知参数: ' + sys.argv[i])
        total = pack(out_path, srcdir, base_asar, replaces)
        print(f'packed {out_path} size={total} replaces={len(replaces)}')
        return 0
    print(__doc__)
    return 1


if __name__ == '__main__':
    sys.exit(main())
