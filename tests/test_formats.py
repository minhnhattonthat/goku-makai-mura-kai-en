"""Format parsers. Synthetic data, so these run on a clone with no ROM."""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import ana
import bms
import gim
import kpd


def test_bms_keeps_glyph_with_zero_trail_byte():
    # 80 00 is the glyph あ: a NUL scan would cut the first string there
    s1, s2 = b"\x80\x00\x80\x01\x00", b"\x07\x02\x01\x80\x01\x00"
    d = struct.pack("<3I", 2, 12, 12 + len(s1)) + s1 + s2
    assert bms.parse(d) == [b"\x80\x00\x80\x01", b"\x07\x02\x01\x80\x01"]


def test_bms_decode_controls():
    t = {b"\x80\x00": "あ", b"\x11": "A"}
    assert bms.decode(b"\x07\x02\x80\x00\x01\x11\x05", t) == "{c2}あ\nA{05}"


def test_tbl_has_core_codes():
    t = bms.load_tbl()
    assert t[b"\x80\x00"] == "あ" and t[b"\x80\x0f"] == "　" and t[b"\x70"] == " "


def _dir(cnt, ent_size, ent_end, sub, data_off, data_size, align):
    h = struct.pack("<IIQQQQQHHH", 1 if cnt else 0, 0x800, ent_size, ent_end, sub, data_off, data_size, cnt, align, 0x3e5)
    return h.ljust(0x800, b"\xff")


def _rec(kind, off, size, name):
    return (struct.pack("<QQQ", kind, off, size) + b"\xff\xff" + name.encode()).ljust(0x80, b"\0")


def test_kpd_walks_subdir_and_nested():
    inner_files = _rec(1, 0, 2, "b.bin").ljust(0x80, b"\0")
    inner = bytearray(struct.pack("<4sIQQQQQQ", b"DPLK", 0x100, 0, 0x10, 0x40, 0x880, 0x8c0, 2).ljust(0x40, b"\0"))
    inner += _dir(1, 0x80, 0x880, 0, 0, 2, 0x10) + inner_files + b"hi"
    root_ents = _rec(0, 0, 0x880, "d").ljust(0x800, b"\0")
    sub = _dir(2, 0x800, 0x1000, 0, 0, len(inner) + 4, 0x800) + (_rec(1, 0, 4, "a.txt") + _rec(1, 0x10, len(inner), "n.kpd")).ljust(0x800, b"\0")
    head = 0x800
    data_start = head + 0x1000 + len(sub)
    d = bytearray(struct.pack("<4sIQQQQQQ", b"DPLK", 0x100, 0, 0x800, head, 0, data_start, 0).ljust(0x800, b"\0"))
    d += _dir(1, 0x800, 0x1000, len(sub), 0, 0, 0x800) + root_ents + sub
    d += b"abcd".ljust(0x10, b"\0") + inner
    assert dict(kpd.walk(bytes(d))) == {"d/a.txt": b"abcd", "d/n.kpd/b.bin": b"hi"}


def test_ana_entries():
    d = bytearray(b"@ANA" + struct.pack("<III", 0x10, 0, 0x100) + struct.pack("<I", 1) + b"\0" * 12)
    d += struct.pack("<II", 0x30, 4) + b"abc\0\0\0\0\0" + b"MIG."
    assert ana.parse(bytes(d)) == [(0x30, 4, "abc")]


def _gim(palette_first):
    """16x1 4bpp GIM with a 2-colour palette: pixel 0 red, pixel 1 green. Header offsets as in the game's files."""
    pal = struct.pack("<HHHHHH", 0x30, 0, 3, 0, 2, 1) + b"\0" * 12 + struct.pack("<III", 0x40, 0x40, 0x50)
    pal = pal.ljust(0x40, b"\0") + struct.pack("<BBBBBBBB", 255, 0, 0, 255, 0, 255, 0, 255)
    img = struct.pack("<HHHHHHHHH", 0x30, 0, 4, 0, 16, 1, 4, 0, 0) + b"\0" * 6 + struct.pack("<III", 0x40, 0x40, 0x50)
    img = img.ljust(0x40, b"\0") + b"\x10" + b"\0" * 15

    def block(t, body):
        return struct.pack("<HHIII", t, 0, len(body) + 16, len(body) + 16, 16) + body

    body = block(5, pal) + block(4, img) if palette_first else block(4, img) + block(5, pal)
    return b"MIG.00.1PSP\0\0\0\0\0" + block(2, block(3, body))


def test_gim_palette_block_either_order():
    for first in (True, False):
        d = _gim(first)
        im = gim.parse(d)[0]
        assert im.pal is not None
        w, h, rows = gim.to_rgba(d, im)
        assert (w, h) == (16, 1) and rows[0][:8] == bytes([255, 0, 0, 255, 0, 255, 0, 255])
