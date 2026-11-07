"""kpd.py: read the DPLK ("KPD") archive format used by datapack.kpd, LAUNCHER.KPD and the nested *.kpd files.

Usage: kpd.py list FILE            top-level tree (offset, size, path)
       kpd.py x FILE OUTDIR        extract every file, descending into nested DPLK files
Format notes: docs/re/kpd.md.
"""
import os
import struct
import sys


def read_dir(d, hdr, prefix, out, dirs):
    """Walk one directory block at file offset hdr. Offsets: see docs/re/kpd.md."""
    _, hdr_size, ent_size, ent_end, sub_size, data_off, data_size, cnt, align, nb = struct.unpack_from("<IIQQQQQHHH", d, hdr)
    assert hdr_size == 0x800 and nb == 0x3e5, hex(hdr)
    ents = hdr + 0x800
    children = hdr + ent_end
    dirs.append((hdr, prefix, cnt, data_off, data_size))
    for i in range(cnt):
        e = ents + i * 0x80
        kind, b, c = struct.unpack_from("<QQQ", d, e)
        name = d[e + 0x1a:e + 0x80].split(b"\0")[0].decode()
        if kind == 1:
            out.append(dict(path=prefix + name, rec=e, off=data_off + b, size=c))
        else:
            read_dir(d, children + b, prefix + name + "/", out, dirs)


def parse(d):
    assert d[:4] == b"DPLK", d[:4]
    size, align, root, dir_size, data_start, data_size = struct.unpack_from("<QQQQQQ", d, 8)
    out, dirs = [], []
    read_dir(d, root, "", out, dirs)
    return out, dirs, data_start


def walk(d, prefix=""):
    """Yield (path, bytes), descending into nested DPLK files."""
    files, _, base = parse(d)
    for f in files:
        b = d[base + f["off"]:base + f["off"] + f["size"]]
        if b[:4] == b"DPLK":
            yield from walk(b, prefix + f["path"] + "/")
        else:
            yield prefix + f["path"], b


if __name__ == "__main__":
    cmd, path = sys.argv[1], sys.argv[2]
    d = open(path, "rb").read()
    if cmd == "list":
        files, _, base = parse(d)
        for f in files:
            print(f"{f['off']:#10x} {f['size']:10d} {f['path']}")
    elif cmd == "x":
        for name, b in walk(d):
            p = os.path.join(sys.argv[3], name)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "wb").write(b)
