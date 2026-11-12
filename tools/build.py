"""build.py: build the English disc image build/goku_en.iso from the dump in rom/.

Usage: build.py [--out ISO] [--identity | --marker [ruler|torture]]
  --marker    every line as `(id) filler` with the line structure of the jp (phase 5 marker build); `ruler`: a long
              ruler per text run, to measure each box; `torture`: every glyph the font has (docs/re/boxes.md)
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
import vwf

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom" / "Goku Makai-Mura Kai (Japan).iso"
USR = "/PSP_GAME/USRDIR/"
US_ROM = ROOT / "rom" / "Ultimate Ghosts 'n Goblins (USA).iso"
FONT = ["font/jfont_00.bft", "font/jfont_00.gim"]
ARCHIVES = [USR + "LAUNCHER/LAUNCHER.KPD", USR + "GOKUMAKAI/datapack.kpd", USR + "REGOKUMAKAI/datapack.kpd"]


def read_files(iso, paths):
    with open(iso, "rb") as f:
        where = {p: (lba, ln) for p, lba, ln, _ in iso9660.listing(f)}
        out = {}
        for p in paths:
            f.seek(where[p][0] * 2048)
            out[p] = f.read(where[p][1])
    return out


def usa_files(paths):
    """{path: bytes} from the USA disc's datapack (D10)."""
    p = USR + "datapack.kpd"
    d = read_files(US_ROM, [p])[p]
    files, _, base = kpd.parse(d)
    return {f["path"]: d[base + f["off"]:base + f["off"] + f["size"]] for f in files if f["path"] in paths}


def font_files():
    """The font both games get: the USA jfont_00 with variable widths."""
    font = usa_files(FONT)
    font["font/jfont_00.bft"] = vwf.make(font["font/jfont_00.bft"], font["font/jfont_00.gim"])
    return font


def edits(archives, marker=None):
    """{iso path: {archive path: bytes}} per archive, or {iso path: bytes} for a plain file (the PRXes).
    Text from script/ (`script.insert`); both games take the USA font with variable widths (tools/vwf.py, docs/re/text.md)."""
    import script  # here, not at the top: script imports build
    out = script.insert(marker)
    font = font_files()
    for game in ("GOKUMAKAI", "REGOKUMAKAI"):
        out[USR + game + "/datapack.kpd"].update(font)
    return out


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


def build(out, identity=False, marker=None):
    check_rom.check()
    archives = read_files(ROM, ARCHIVES)
    todo = identity_edits(archives) if identity else edits(archives, marker)
    repl = {p: e if isinstance(e, bytes) else kpd.rebuild(archives[p], e) for p, e in todo.items()}
    if not identity:
        # the changed archive files, unpacked: work/<out stem>/<re|go>/pkdata/..., the BMS_DIR for warp.py's message tours
        for p, e in todo.items():
            game = {"GOKUMAKAI": "go", "REGOKUMAKAI": "re"}.get(p.split("/")[-2])
            for name, b in (e.items() if game and isinstance(e, dict) else ()):
                f = ROOT / "work" / out.stem / game / name
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_bytes(b)
    out.parent.mkdir(parents=True, exist_ok=True)
    iso9660.patch(str(ROM), str(out), repl)
    with open(out, "rb") as f:
        return hashlib.file_digest(f, "sha1").hexdigest()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "build" / "goku_en.iso")
    ap.add_argument("--identity", action="store_true")
    ap.add_argument("--marker", nargs="?", const="id", choices=["id", "ruler", "torture"],
                    help="every line as `(id) filler` (phase 5); `ruler`: a 100-character ruler, `torture`: every glyph")
    a = ap.parse_args()
    sha = build(a.out, a.identity, a.marker)
    print(a.out, sha)
    if a.identity:
        want = (ROOT / "rom.sha1").read_text().split()[0]
        print("identical" if sha == want else f"DIFFERS from the dump ({want})")
        sys.exit(sha != want)
