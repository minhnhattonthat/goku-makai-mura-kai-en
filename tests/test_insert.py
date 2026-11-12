"""Phase 5 inserter: script/ -> .bms and PRX bytes, the marker text, the variable-width font."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import bms
import build
import script
import sfo
import vwf

need_roms = pytest.mark.skipif(not (build.ROM.is_file() and build.US_ROM.is_file()), reason="needs the dumps in rom/")
CODES = re.compile(r"\{[^}]*\}|\n")


def test_marker_keeps_codes_and_lines():
    r = {"id": "a02:4", "jp": "セーブしますか？\n{c:01}{05}はい　{05}{02}{04}{06}いいえ{03}"}
    m = script.marker(r)
    assert m.startswith("(a02:4) ") and CODES.findall(m) == CODES.findall(r["jp"]) and "　" in m
    assert script.marker(r, script.RULER).count(script.RULER) == 3


@need_roms
def test_insert_writes_every_row():
    """Each .bms decodes back to its rows' text, a Kai `inherit` row carries its source row's en, PRX slots keep their size."""
    t = bms.load_tbl()
    docs = script.load()
    out = script.insert()
    for game, files in docs.items():
        for name, doc in files.items():
            if name == "prx":
                d = out[doc["archive"]]
                orig = script.prx_bytes(game)
                assert len(d) == len(orig)
                for r in doc["strings"]:
                    want = r["jp"] if r["status"] in ("empty", "keep") else script.en_text(r, docs)
                    at = int(r["id"][4:], 16)
                    # follow each of the row's table pointers (a long string moves; script.prx_patch)
                    ptrs = script.prx_pointers(orig, game, at)
                    for o in [int.from_bytes(d[p:p + 4], "little") + 0x80 for p in ptrs] or [at]:   # PRX_SJIS: in place
                        assert d[o:d.index(b"\0", o)].decode() == want, r["id"]
                continue
            if name == "sfo":
                assert sfo.read(out[doc["archive"]])["TITLE"][4] == script.en_text(doc["strings"][0], docs)
                continue
            got = [bms.decode(s, t) for s in bms.parse(out[doc["archive"]][doc["path"]])]
            assert len(got) == len(doc["strings"])
            for r, g in zip(doc["strings"], got):
                assert g == (r["jp"] if r["status"] in ("empty", "keep") else script.en_text(r, docs)), r["id"]
    assert script.en_text({"status": "inherit", "same": "go/a30:1"}, docs) == script.en_text(
        next(r for r in docs["go"]["a30"]["strings"] if r["id"] == "a30:1"), docs)


@need_roms
def test_lint_clean():
    """Width gate (docs/re/boxes.md): no translated row over its box; the official text fits too."""
    import lint
    errors, warnings, _ = lint.run()
    assert errors == [] and warnings == []


@need_roms
def test_vwf_font():
    f = build.font_files()
    bft, t = f["font/jfont_00.bft"], bms.load_tbl()
    assert vwf.line_widths("あ", bft, t) == [18]   # kana untouched
    w = lambda s: vwf.line_widths(s, bft, t)[0]
    assert w("i") < w("m") <= 12 and w("0") == w("1") and w(" ") == vwf.SPACE
    assert vwf.line_widths("ab\nc{c:01}", bft, t) == [w("ab"), w("c")]
