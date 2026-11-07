"""bms.py: read the .bms message files. Usage: bms.py FILE...   prints every string, decoded.

Layout: u32 count, u32 offset[count], then NUL-terminated strings (docs/re/text.md).
Stream: 0x80-0x87 leads a two-byte glyph, other bytes >= 0x09 are one-byte glyphs, bytes below 0x09 are control codes.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_tbl(path=ROOT / "tbl/jp.tbl"):
    t = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        k, v = line.split("=", 1)
        t[bytes.fromhex(k)] = v
    return t


def parse(d):
    n = struct.unpack_from("<I", d, 0)[0]
    offs = struct.unpack_from(f"<{n}I", d, 4) + (len(d),)
    # bounded by the next offset: a NUL scan would stop inside the glyph code 80 00
    return [d[offs[i]:offs[i + 1]].removesuffix(b"\0") for i in range(n)]


def decode(b, t):
    out, i = [], 0
    while i < len(b):
        c = b[i]
        if 0x80 <= c < 0x88:
            out.append(t.get(b[i:i + 2], f"[{b[i:i + 2].hex()}]"))
            i += 2
        elif c < 9:
            if c == 1:
                out.append("\n")
            elif c == 7:
                out.append(f"{{c{b[i + 1]}}}")
                i += 1
            else:
                out.append(f"{{{c:02x}}}")
            i += 1
        else:
            out.append(t.get(b[i:i + 1], f"[{c:02x}]"))
            i += 1
    return "".join(out)


if __name__ == "__main__":
    t = load_tbl()
    for f in sys.argv[1:]:
        print("=====", f)
        for i, s in enumerate(parse(open(f, "rb").read())):
            print(f"{i:3d}: {decode(s, t)!r}")
