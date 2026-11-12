"""build.py: build the English disc image build/goku_en.iso from the dump in rom/.

Usage: build.py [--out ISO] [--identity]
  --identity  push every file of every archive back through the rebuild unchanged; the output must equal the dump (phase 3 test)
Steps: check the dump against rom.sha1, rebuild each DPLK archive with its edits (tools/kpd.py rebuild), swap the changed
files into the ISO (tools/iso9660.py patch; a grown file moves to the end of the image)."""
import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_rom
import iso9660
import kpd

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom" / "Goku Makai-Mura Kai (Japan).iso"
USR = "/PSP_GAME/USRDIR/"
ARCHIVES = [USR + "LAUNCHER/LAUNCHER.KPD", USR + "GOKUMAKAI/datapack.kpd", USR + "REGOKUMAKAI/datapack.kpd"]


def read_files(iso, paths):
    with open(iso, "rb") as f:
        where = {p: (lba, ln) for p, lba, ln, _ in iso9660.listing(f)}
        out = {}
        for p in paths:
            f.seek(where[p][0] * 2048)
            out[p] = f.read(where[p][1])
    return out


def edits(archives):
    """{iso path: {archive path: bytes}}. Empty until the text and graphics phases add their output."""
    return {}


def identity_edits(archives):
    """Every file of every archive, nested ones included, replaced by its own bytes."""
    def all_files(d):
        files, _, base = kpd.parse(d)
        out = {}
        for f in files:
            b = d[base + f["off"]:base + f["off"] + f["size"]]
            out.update({f["path"] + "/" + k: v for k, v in all_files(b).items()} if b[:4] == b"DPLK" else {f["path"]: b})
        return out
    return {p: all_files(d) for p, d in archives.items()}


def build(out, identity=False):
    check_rom.check()
    archives = read_files(ROM, ARCHIVES)
    todo = (identity_edits if identity else edits)(archives)
    repl = {p: kpd.rebuild(archives[p], e) for p, e in todo.items()}
    out.parent.mkdir(parents=True, exist_ok=True)
    iso9660.patch(str(ROM), str(out), repl)
    with open(out, "rb") as f:
        return hashlib.file_digest(f, "sha1").hexdigest()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "build" / "goku_en.iso")
    ap.add_argument("--identity", action="store_true")
    a = ap.parse_args()
    sha = build(a.out, a.identity)
    print(a.out, sha)
    if a.identity:
        want = (ROOT / "rom.sha1").read_text().split()[0]
        print("identical" if sha == want else f"DIFFERS from the dump ({want})")
        sys.exit(sha != want)
