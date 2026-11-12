"""vwf.py: a variable-width jfont_00.bft: each ASCII glyph's rect trimmed to its ink plus GAP px, so the game advances by it.

Usage: vwf.py BFT GIM [--out OUT.bft]   prints code, char, old and new x/w
The bft entry {0, x, y, w, h} is both the sheet rect and the advance (the game's own punctuation has w 8-11; docs/re/text.md).
Digits keep one width (all trimmed alike) so numbers line up; kana, kanji and fullwidth cells stay as they are."""
import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gim

GAP = 1          # px after the ink; the outline is already inside the ink
SPACE = 5        # advance of the half space (code 70)
LETTERS = [*range(0x10, 0x2A), *range(0x30, 0x4A), *range(0x50, 0x62)]   # A-Z a-z, punctuation incl. the 18 px + & # %
DIGITS = range(0x71, 0x7B)


def entry(b, c):
    return struct.unpack_from("<5H", b, 0x2c + c * 10)


def ink(px, w, x, y, cw, ch):
    cols = [i for i in range(cw) if any(px[((y + j) * w + x + i) * 4 + 3] for j in range(ch))]
    return cols[0], cols[-1]


def make(bft, gim_bytes):
    gw, _, rows = gim.to_rgba(gim_bytes, gim.parse(gim_bytes)[0])
    px = b"".join(rows)
    out = bytearray(bft)
    put = lambda c, x, w: struct.pack_into("<5H", out, 0x2c + c * 10, *(lambda e: (e[0], x, e[2], w, e[4]))(entry(bft, c)))
    for c in LETTERS:
        z, x, y, w, h = entry(bft, c)
        l, r = ink(px, gw, x, y, w, h)
        put(c, x + l, r - l + 1 + GAP)
    spans = [ink(px, gw, *entry(bft, c)[1:]) for c in DIGITS]
    l, r = min(s[0] for s in spans), max(s[1] for s in spans)
    for c in DIGITS:
        z, x, y, w, h = entry(bft, c)
        put(c, x + l, r - l + 1 + GAP)
    z, x, y, w, h = entry(bft, 0x70)
    put(0x70, x, SPACE)
    for c in range(0x80):   # self-check: every new rect stays inside the old one
        o, n = entry(bft, c), entry(out, c)
        assert o[1] <= n[1] and n[1] + n[3] <= o[1] + o[3] + GAP, (hex(c), o, n)
    return bytes(out)


def advance(bft, code):
    """Advance in font px of one glyph code (1 or 2 bytes): its bft w. 2-byte codes: lead 80-87 picks a page (u32 at 0x0c)."""
    if len(code) == 1:
        return entry(bft, code[0])[3]
    page = struct.unpack_from("<I", bft, 0x0c + (code[0] - 0x80) * 4)[0]
    return struct.unpack_from("<5H", bft, page + code[1] * 10)[3]


def line_widths(text, bft, table):
    """Font px of each line of a script/ text (`\\n` breaks; control codes take no room)."""
    out = []
    for line in text.split("\n"):
        b = table.encode(line)
        i, w = 0, 0
        while i < len(b):
            if b[i] < 0x09:
                i += 1 + table.ctrl[bytes([b[i]])][1]
            elif b[i] >= 0x80:
                w += advance(bft, b[i:i + 2]); i += 2
            else:
                w += advance(bft, b[i:i + 1]); i += 1
        out.append(w)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("bft"); ap.add_argument("gim"); ap.add_argument("--out")
    a = ap.parse_args()
    b = Path(a.bft).read_bytes()
    n = make(b, Path(a.gim).read_bytes())
    for c in range(0x80):
        if entry(b, c) != entry(n, c):
            print(f"{c:02X} x {entry(b, c)[1]}->{entry(n, c)[1]} w {entry(b, c)[3]}->{entry(n, c)[3]}")
    if a.out:
        Path(a.out).write_bytes(n)
