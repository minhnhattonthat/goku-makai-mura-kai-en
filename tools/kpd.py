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
            out.append(dict(path=prefix + name, rec=e, off=data_off + b, size=c, doff=data_off))
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


def rebuild(d, repl):
    """Return archive d with files replaced, repl = {path: bytes}; a path may reach into a nested DPLK ("pkdata/x.kpd/a.bms").

    A file that outgrows its aligned slot shifts every later file by the growth, so each directory's data region stays
    contiguous and holds its own files (the layout the original archives have). Directory blocks and hashes never change."""
    if not repl:
        return d
    files, dirs, base = parse(d)
    by_path = {f["path"]: f for f in files}
    flat = {}
    for key, b in repl.items():
        if key in by_path:
            flat[key] = b
            continue
        outer = next((p for p in by_path if key.startswith(p + "/")), None)
        assert outer, f"no such file: {key}"
        flat.setdefault(outer, {})[key[len(outer) + 1:]] = b
    for p, v in flat.items():
        if isinstance(v, dict):
            f = by_path[p]
            flat[p] = rebuild(d[base + f["off"]:base + f["off"] + f["size"]], v)
    align = struct.unpack_from("<Q", d, 0x10)[0]
    up = lambda n: -(-n // align) * align
    grow = sorted((by_path[p]["off"], up(len(b)) - up(by_path[p]["size"])) for p, b in flat.items())
    shift = lambda x: x + sum(g for o, g in grow if o < x)
    data_size = struct.unpack_from("<Q", d, 0x30)[0]
    new_size = shift(data_size)
    order = sorted(files, key=lambda f: f["off"])
    out = bytearray(d[:base + order[0]["off"]]) + bytearray(new_size - order[0]["off"])
    for i, f in enumerate(order):
        new = flat.get(f["path"])
        end = order[i + 1]["off"] if i + 1 < len(order) else data_size
        assert f["off"] + up(f["size"]) <= end, f"{f['path']}: slot not padded to the alignment"  # true of every game archive
        if new is None:  # copy the file and its original padding
            out[base + shift(f["off"]):base + shift(f["off"]) + end - f["off"]] = d[base + f["off"]:base + end]
        else:
            out[base + shift(f["off"]):base + shift(f["off"]) + len(new)] = new
        struct.pack_into("<QQ", out, f["rec"] + 8, shift(f["off"]) - shift(f["doff"]), f["size"] if new is None else len(new))
    for hdr, _, _, doff, dsize in dirs:
        struct.pack_into("<QQ", out, hdr + 0x20, shift(doff), shift(doff + dsize) - shift(doff))
    struct.pack_into("<Q", out, 0x08, base + new_size)
    struct.pack_into("<Q", out, 0x30, new_size)
    return bytes(out)


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
