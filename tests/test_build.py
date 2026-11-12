"""Identity build (phase 3): every archive pushed back through kpd.rebuild unchanged gives the dump, byte for byte."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build


@pytest.mark.skipif(not build.ROM.is_file(), reason="needs the dump in rom/")
def test_identity_build_equals_dump():
    sha = build.build(ROOT / "build" / "identity.iso", identity=True)
    assert sha == (ROOT / "rom.sha1").read_text().split()[0]
