"""release.py: build, verify and package the English patch (references/pipeline.md §Release of the skill).

Usage: release.py [--version 1.0] [--force]
Stops at the first failing step: build -> check (tests + lint) -> diffcheck (write scope; also proves no debug code
ships: the build writes only text, font, textures, PRX save strings and their pointer table, and tools/debug/warp.py
pokes emulator RAM only) -> smoke boot -> jp_left on every built .bms -> qa_gate check on every work/qa/**/manifest.tsv
-> cover + textcover -> docs/polish.md all ticked -> no template placeholder in README.md -> xdelta3 patch of the
Japanese ISO -> re-apply it to the original and compare -> release/<name>_v<version>.zip (ZIP_STORED: patch + README.txt).
Refuses to overwrite an existing version without --force. The playable image stays in build/goku_en.iso.
"""
import argparse
import glob
import hashlib
import re
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill import SKILL

ROOT = Path(__file__).resolve().parents[1]
ISO = ROOT / "build" / "goku_en.iso"
NAME = "Goku_Makaimura_Kai_EN"
PY = [sys.executable, "-X", "utf8"]


def step(name, cmd):
    print(f"== {name}", flush=True)
    if subprocess.call(cmd, cwd=ROOT):
        sys.exit(f"release: {name} failed")


def hashes(p):
    crc, sha = 0, hashlib.sha1()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            crc = zlib.crc32(b, crc)
            sha.update(b)
    return f"{crc:08X}", sha.hexdigest()


def jp_left(work):
    """Every .bms of the built ISO's archives through the skill's jp_left.py with the game's table."""
    import build
    import kpd
    out = work / "bms"
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for arc, d in build.read_files(ISO, build.ARCHIVES).items():
        for path, data in kpd.walk(d):
            if path.endswith(".bms"):
                f = out / f"{n:03d}_{Path(path).name}"
                f.write_bytes(data)
                step(f"jp_left {Path(arc).parent.name}/{path}",
                     PY + [f"{SKILL}/scripts/jp_left.py", str(f), "--tbl", "tbl/jp.tbl"])
                n += 1
    if not n:
        sys.exit("release: no .bms found in the build")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", default="1.0")
    ap.add_argument("--force", action="store_true", help="overwrite this version's files in release/")
    a = ap.parse_args()
    rel = ROOT / "release"
    zpath, patch = rel / f"{NAME}_v{a.version}.zip", rel / f"{NAME}_v{a.version}.xdelta"
    if (zpath.exists() or patch.exists()) and not a.force:
        sys.exit(f"release: {zpath.name} exists; pass --force to overwrite it")
    work = ROOT / "work" / "release"
    work.mkdir(parents=True, exist_ok=True)
    orig = ROOT / "rom" / "Goku Makai-Mura Kai (Japan).iso"

    step("build", PY + ["tools/build.py"])
    step("check", PY + ["tools/check.py"])
    step("diffcheck", PY + ["tools/diffcheck.py", str(ISO)])
    step("smoke", PY + [f"{SKILL}/scripts/emu.py", str(ISO), "--out", "work/qa/smoke_en",
                        "--route", "tools/routes/boot.txt", "--smoke"])
    jp_left(work)
    for m in sorted(glob.glob(str(ROOT / "work/qa/**/manifest.tsv"), recursive=True)):
        step(f"qa_gate {Path(m).parent.name}", PY + [f"{SKILL}/scripts/qa_gate.py", "check", m,
                                                    str(Path(m).parent / "verdicts")])
    step("cover", PY + ["tools/cover.py", "--tour", "work/qa/tour", "work/qa/p9"])
    step("textcover", PY + [f"{SKILL}/scripts/textcover.py", "work/qa/cover", "work/qa/cover/strings.tsv",
                            "--waive", "docs/text_unshown.tsv"])
    if re.search(r"^- \[ \]", (ROOT / "docs/polish.md").read_text(encoding="utf8"), re.M):
        sys.exit("release: docs/polish.md has unticked lines")
    left = re.findall(r"<[^>\n]*>", (ROOT / "README.md").read_text(encoding="utf8"))   # the template's <...> fields
    if left:
        sys.exit(f"release: README.md still has template placeholders: {sorted(set(left))}")

    print("== patch", flush=True)
    rel.mkdir(exist_ok=True)
    patch.unlink(missing_ok=True)
    # -B the image size: by default xdelta only matches within 64 MB, and the rebuilt archives moved data
    step("xdelta3 encode", ["xdelta3", "-e", "-9", "-B", str(orig.stat().st_size), "-s", str(orig), str(ISO), str(patch)])
    back = work / "reapplied.iso"
    back.unlink(missing_ok=True)
    step("xdelta3 decode", ["xdelta3", "-d", "-s", str(orig), str(patch), str(back)])
    crc, sha = hashes(ISO)
    if hashes(back) != (crc, sha):
        sys.exit("release: the re-applied patch does not give the build")
    back.unlink()
    readme = (ROOT / "docs/release_readme.txt").read_text(encoding="utf8").format(
        version=a.version, patch=patch.name, size=ISO.stat().st_size, crc32=crc, sha1=sha)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as z:
        z.write(patch, patch.name)
        z.writestr("README.txt", readme.replace("\n", "\r\n"))
    print(f"{zpath}\n  patch {patch.stat().st_size} bytes, sha1 {hashes(patch)[1]}\n  patched CRC32 {crc}, sha1 {sha}")


if __name__ == "__main__":
    main()
