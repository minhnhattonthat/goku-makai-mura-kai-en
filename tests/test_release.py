"""release.py's guards: --help never builds, an existing version is never overwritten without --force."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = [sys.executable, "-X", "utf8", str(ROOT / "tools" / "release.py")]


def test_help_does_not_build():
    r = subprocess.run(REL + ["--help"], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert r.returncode == 0 and "== build" not in r.stdout


def test_refuses_to_overwrite_a_version():
    z = ROOT / "release" / "Goku_Makaimura_Kai_EN_v0.0-test.zip"
    z.parent.mkdir(exist_ok=True)
    z.write_bytes(b"")
    try:
        r = subprocess.run(REL + ["--version", "0.0-test"], cwd=ROOT, capture_output=True, text=True, timeout=30)
        assert r.returncode != 0 and "--force" in r.stderr and "== build" not in r.stdout
    finally:
        z.unlink()
