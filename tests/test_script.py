"""script/: the phase 4 roundtrip and coverage test against the dumps, plus the dump merge rule (no ROM needed)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build
import script


def test_merge_keeps_work_and_refreshes_prefill():
    r = {"id": "a:1", "jp": "あ", "us": "A2"}
    assert not script.merge(r, {"id": "a:1", "jp": "あ", "us": "A", "en": "A", "status": "official"}) and r["en"] == "A2"
    r = {"id": "a:1", "jp": "い", "status": "new"}
    assert script.merge(r, {"id": "a:1", "jp": "あ", "en": "Hi", "status": "done", "notes": "n"})
    assert (r["en"], r["status"], r["notes"]) == ("Hi", "recheck", "n")


@pytest.mark.skipif(not (build.ROM.is_file() and script.US_ISO.is_file()), reason="needs the dumps in rom/")
def test_script_roundtrip_and_coverage():
    assert script.check() == []
