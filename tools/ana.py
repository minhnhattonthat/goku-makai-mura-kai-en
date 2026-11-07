"""ana.py: @ANA texture container (a list of named GIMs).

Layout: "@ANA", u32 0x10, u32 size, u32 0x100, u32 count, 12 pad, then count entries of {u32 off, u32 size, char name[8]}.
Usage: ana.py x FILE.ana OUTDIR    dump every GIM and a PNG of it as NN_name.gim/.png
"""
import os
import struct
import sys


def parse(d):
    assert d[:4] == b"@ANA", d[:4]
    n = struct.unpack_from("<I", d, 0x10)[0]
    out = []
    for i in range(n):
        off, size = struct.unpack_from("<II", d, 0x20 + i * 0x10)
        name = d[0x28 + i * 0x10:0x30 + i * 0x10].split(b"\0")[0].decode()
        out.append((off, size, name))
    return out


if __name__ == "__main__":
    from skill import SCRIPTS
    sys.path.insert(0, SCRIPTS)
    import gim
    d = open(sys.argv[2], "rb").read()
    os.makedirs(sys.argv[3], exist_ok=True)
    for i, (off, size, name) in enumerate(parse(d)):
        b = d[off:off + size]
        stem = os.path.join(sys.argv[3], f"{i:02d}_{name}")
        open(stem + ".gim", "wb").write(b)
        for im in gim.parse(b)[:1]:
            w, h, rows = gim.to_rgba(b, im)
            gim.save_png(stem + ".png", w, h, rows)
