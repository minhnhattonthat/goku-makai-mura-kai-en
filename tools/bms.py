"""bms.py: read and write the .bms message files. Usage: bms.py FILE...   prints every string, decoded.

Layout: u32 count, u32 offset[count], then the strings, each ending in 00 (docs/re/text.md).
Stream: 0x80-0x87 leads a two-byte glyph, other bytes >= 0x09 are one-byte glyphs, bytes 00-08 are control codes (tbl/jp.tbl).
Text form: tbl.py tokens, with {n} shown as a real newline.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tbl import Table

ROOT = Path(__file__).resolve().parents[1]


def load_tbl(path=ROOT / "tbl/jp.tbl"):
    return Table.load(path)


def parse(d):
    n = struct.unpack_from("<I", d, 0)[0]
    offs = struct.unpack_from(f"<{n}I", d, 4) + (len(d),)
    # bounded by the next offset: a NUL scan would stop inside the glyph code 80 00
    return [d[offs[i]:offs[i + 1]].removesuffix(b"\0") for i in range(n)]


def build(strings):
    """Inverse of parse: build(parse(d)) == d for every file in the game."""
    offs, body = [], b""
    for s in strings:
        offs.append(4 + 4 * len(strings) + len(body))
        body += s + b"\0"
    return struct.pack(f"<I{len(strings)}I", len(strings), *offs) + body


def decode(b, t):
    return t.decode(b, 0, len(b))[0].replace("{n}", "\n")


def encode(s, t):
    return t.encode(s.replace("\n", "{n}"))


if __name__ == "__main__":
    t = load_tbl()
    for f in sys.argv[1:]:
        print("=====", f)
        for i, s in enumerate(parse(open(f, "rb").read())):
            print(f"{i:3d}: {decode(s, t)!r}")
