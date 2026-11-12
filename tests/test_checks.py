"""Phase 7 checks: the build's write scope (tools/diffcheck.py), the PRX repoint, the lint's glossary parse."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build
import diffcheck
import iso9660
import kpd
import lint
import script
import sfo

need_roms = pytest.mark.skipif(not (build.ROM.is_file() and build.US_ROM.is_file()), reason="needs the dumps in rom/")


def test_glossary_terms():
    terms = {j: (en, avoid) for jp, en, avoid in lint.glossary() for j in jp}
    assert terms["最強の魔力"] == (["ultimate power"], ["mightiest magic"])
    assert "第Nの魔界門" not in terms and "大魔王" in terms
    order = [jp[0] for jp, _, _ in lint.glossary()]
    assert order.index("魔力水晶") < order.index("魔力")   # longest first, so the longer term hides the shorter


@need_roms
def test_prx_patch_moves_and_repoints():
    docs = script.load()
    rows = docs["go"]["prx"]["strings"]
    texts = [script.en_text(r, docs).encode() for r in rows]   # English leaves free tails to move into
    i = next(k for k, r in enumerate(rows) if r["id"] == "prx:0x349da8")   # 19-byte slot
    texts[i] = b"X" * 30
    d = script.prx_patch("go", rows, texts)
    (p,) = script.prx_pointers(script.prx_bytes("go"), "go", 0x349da8)
    o = int.from_bytes(d[p:p + 4], "little") + 0x80
    assert o != 0x349da8 and d[o:o + 31] == b"X" * 30 + b"\0"
    with pytest.raises(ValueError):
        script.prx_patch("go", rows, [b"X" * 400 if k == i else t for k, t in enumerate(texts)])


@need_roms
def test_build_writes_only_its_ranges(tmp_path):
    iso = tmp_path / "en.iso"
    build.build(iso)
    assert diffcheck.check(iso) == []
    prx_path = build.USR + "GOKUMAKAI/GOKUMAKAI.PRX"
    got = build.read_files(iso, [script.SFO, prx_path])
    assert sfo.read(got[script.SFO])["TITLE"][4] == "Ultimate Ghosts 'n Goblins Kai"
    assert got[prx_path][0x34A070:0x34A070 + 14] == b"New Save Data\0"
    with open(iso, "rb") as f:
        where = {p: lba for p, lba, _, _ in iso9660.listing(f)}
    prx = where[prx_path] * 2048
    other = where[build.USR + "GOKUMAKAI/movie/" + next(
        p.split("/")[-1] for p in where if "/GOKUMAKAI/movie/" in p)] * 2048    # a file the build never touches
    with open(iso, "r+b") as f:
        for at in (prx + 0x1000, other):    # PRX code, not the save strings
            f.seek(at)
            b = f.read(1)
            f.seek(at)
            f.write(bytes([b[0] ^ 0xFF]))
        f.seek(prx + script.PRX_PTRS["go"][0])
        f.write(bytes(4))                   # a table word pointing outside the region
        f.seek(prx + script.PRX["go"][0] + 4)
        f.write("魔界村".encode())          # Japanese UTF-8 inside the region
        f.seek(prx + script.PRX_SJIS["go"][0])
        f.write("新規作成".encode("cp932") + b"\0")   # Shift-JIS back in the new-data title slot
        arch = build.USR + "GOKUMAKAI/datapack.kpd"
        a = build.read_files(iso, [arch])[arch]
        files, _, base = kpd.parse(a)
        edited = build.edits(build.read_files(build.ROM, build.ARCHIVES))[arch]
        m = next(x for x in files if x["size"] > 16 and a[base + x["off"]:base + x["off"] + 4] != b"DPLK"
                 and not any(k == x["path"] or k.startswith(x["path"] + "/") for k in edited))   # one the build leaves alone
        f.seek(where[arch] * 2048 + base + m["off"] + 8)
        b = f.read(1)
        f.seek(where[arch] * 2048 + base + m["off"] + 8)
        f.write(bytes([b[0] ^ 0xFF]))
    bad = diffcheck.check(iso)
    assert any("GOKUMAKAI.PRX: bytes changed outside" in x for x in bad)
    assert any("movie/" in x for x in bad)
    assert any("not a string start in the region" in x for x in bad)
    assert any("Japanese UTF-8 left" in x for x in bad)
    assert any("Japanese Shift-JIS left" in x for x in bad)
    assert any(f"{arch}: {m['path']}" in x and "not to the bytes" in x for x in bad)


def prx_refs(d):
    """(file offset, target vaddr) of every R_MIPS_32 word and HI16/LO16 (lui + addiu/ori/load) pair into segment 0,
    from the PRX's own relocation sections (type 0x700000A0)."""
    import struct
    e_phoff, e_shoff = struct.unpack_from("<II", d, 0x1C)
    e_phnum, _, e_shnum = struct.unpack_from("<HHH", d, 0x2C)
    ph = [struct.unpack_from("<8I", d, e_phoff + 32 * i) for i in range(e_phnum)]
    sh = [struct.unpack_from("<10I", d, e_shoff + 40 * i) for i in range(e_shnum)]
    out, his = [], []
    for s in (s for s in sh if s[1] == 0x700000A0):
        for k in range(s[4], s[4] + s[5], 8):
            off, info = struct.unpack_from("<II", d, k)
            t, ab = info & 0xFF, (info >> 16) & 0xFF
            at = ph[(info >> 8) & 0xFF][1] + off
            w = int.from_bytes(d[at:at + 4], "little")
            if t == 5:
                his.append(at)
            elif t == 6:
                lo = ((w & 0xFFFF) ^ 0x8000) - 0x8000
                out += [(h, ((int.from_bytes(d[h:h + 4], "little") & 0xFFFF) << 16) + lo) for h in his if ab == 0]
                his = []
            elif t == 2 and ab == 0:
                out.append((at, w))
    return out


@need_roms
def test_prx_region_read_only_through_the_table():
    """Moving a string is safe only if nothing but PRX_PTRS points into the save-dialog region (phase-7 Minor 5)."""
    for g in ("re", "go"):
        rr = prx_refs(script.prx_bytes(g))
        (r0, r1), (t0, t1) = script.PRX[g], script.PRX_PTRS[g]
        assert [(a, v) for a, v in rr if r0 <= v + 0x80 < r1 and not t0 <= a < t1] == []
        assert len([a for a, _ in rr if t0 <= a < t1]) == (t1 - t0) // 4   # every table word is relocated
        assert any(v + 0x80 in script.PRX_SJIS[g] for _, v in rr)          # the scan does see lui/addiu pairs


@need_roms
def test_gfx_keeps_jp_button_icons():
    """The USA button icons swap circle and cross; every edited ANA keeps the original's button0 GIMs."""
    import ana
    import gfx
    e = gfx.edits()
    for game, members in e.items():
        own = gfx.tree(build.ROM, gfx.ARCH[game])
        for m, (b, _) in members.items():
            if not m.endswith(".ana"):
                continue
            old, new = ana.parse(own[m]), ana.parse(b)
            assert [(o, s, n) for o, s, n in old] == new   # offsets, sizes, names unchanged
            for o, s, n in new:
                if n in gfx.KEEP_JP:
                    assert b[o:o + s] == own[m][o:o + s], (game, m, n)
    assert "18_op_wor0" in e["re"][gfx.D2.format("play_res", "a10", "a10", "ana")][1]


@need_roms
def test_prx_alignment_and_sjis_slot():
    docs = script.load()
    rows = docs["go"]["prx"]["strings"]
    texts = [script.en_text(r, docs).encode() for r in rows]
    d = script.prx_patch("go", rows, texts)
    for r in rows:   # every moved string lands 4-aligned
        for p in script.prx_pointers(script.prx_bytes("go"), "go", int(r["id"][4:], 16)):
            assert (int.from_bytes(d[p:p + 4], "little") + 0x80) % 4 == 0
    i = next(k for k, r in enumerate(rows) if r["id"] == "prx:0x34a070")
    with pytest.raises(ValueError):   # no pointer to move it by: must fit its own slot
        script.prx_patch("go", rows, [b"X" * 16 if k == i else t for k, t in enumerate(texts)])
