"""Phase 7 checks: the build's write scope (tools/diffcheck.py), the PRX repoint, the lint's glossary parse."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build
import diffcheck
import iso9660
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
    bad = diffcheck.check(iso)
    assert any("GOKUMAKAI.PRX: bytes changed outside" in x for x in bad)
    assert any("movie/" in x for x in bad)
    assert any("not a string start in the region" in x for x in bad)


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
