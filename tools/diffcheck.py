"""diffcheck.py: the build writes only where it should (the romdiff check, per layer of the disc).

Usage: diffcheck.py [BUILT_ISO]   (default build/goku_en.iso); exit 1 on any problem
- ISO: every changed byte is a changed file's data (old or new extent), its directory record (LBA, size) or the volume
  size in the PVD; no file was added or dropped; the files that differ are exactly the ones build.edits() replaces.
  The whole image is scanned, past the original's end too.
- Archives: the same member list as the original; a member that differs holds exactly the bytes build.edits() gives it
  (.bms text, the font, tools/gfx.py textures).
- PRX: bytes differ only in the save-dialog region (script.PRX), its pointer table (script.PRX_PTRS) and the Shift-JIS
  new-data title slots (script.PRX_SJIS); every table word points at a string start in the region; no Japanese UTF-8 or
  Shift-JIS run (3+ characters) is left.
- PARAM.SFO: only its TITLE differs.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build
import iso9660
import kpd
import script
import sfo

CHUNK = 1 << 20


def files(iso):
    with open(iso, "rb") as f:
        return {p: (lba, ln, pos) for p, lba, ln, pos in iso9660.listing(f)}


def iso_problems(orig, new, changed):
    """changed: {path} of files whose bytes differ. Problems as strings."""
    a, b = files(orig), files(new)
    bad = [f"ISO: {p} added or dropped" for p in sorted(set(a) ^ set(b))]
    allowed = [(16 * 2048 + 80, 16 * 2048 + 88)]
    for p in changed:
        for lba, ln, pos in (a[p], b[p]):
            allowed.append((lba * 2048, (lba + -(-ln // 2048)) * 2048))
            allowed += [(pos + 2, pos + 10), (pos + 10, pos + 18)]
    with open(orig, "rb") as fa, open(new, "rb") as fb:
        end = max(fa.seek(0, 2), fb.seek(0, 2))   # past the original's end too (grown files append there)
        fa.seek(0)
        fb.seek(0)
        at = 0
        while at < end:
            x, y = fa.read(CHUNK), fb.read(CHUNK)
            n = max(len(x), len(y))
            x, y = x.ljust(n, b"\0"), y.ljust(n, b"\0")   # missing bytes count as 0
            if x != y and not any(s <= at and at + len(x) <= e for s, e in allowed):
                for i in range(len(x)):
                    if x[i] != y[i] and not any(s <= at + i < e for s, e in allowed):
                        bad.append(f"ISO: byte {at + i:#x} changed outside every allowed range")
                        break
            at += len(x)
    return bad


def check(new):
    bad = []
    want = build.edits(build.read_files(build.ROM, build.ARCHIVES))
    paths = list(files(build.ROM))
    orig_b, new_b = build.read_files(build.ROM, paths), build.read_files(new, paths)
    changed = {p for p in paths if orig_b[p] != new_b[p]}
    if changed != set(want):
        bad.append(f"ISO: changed files {sorted(changed)} != the files the build edits {sorted(want)}")
    bad += iso_problems(build.ROM, new, changed)
    for p in sorted(changed & set(want)):
        o, n = orig_b[p], new_b[p]
        if p == script.SFO:
            if n != sfo.set_str(o, "TITLE", sfo.read(n)["TITLE"][4]):
                bad.append(f"{p}: changed beyond its TITLE")
            continue
        if p.endswith(".PRX"):
            game = next(g for g, n in script.GAMES.items() if p.endswith("/" + n + ".PRX"))
            (r0, r1), (t0, t1) = script.PRX[game], script.PRX_PTRS[game]
            if len(o) != len(n):
                bad.append(f"{p}: size changed")
            bad += [f"{p}: Japanese UTF-8 left at {m.start():#x}" for m in script.JP_UTF8.finditer(n)]
            bad += [f"{p}: Japanese Shift-JIS left at {o:#x}" for o in script.sjis_runs(n)]
            keep = sorted([(0, r0), (r1, t0), (t1, len(o))])
            for s in script.PRX_SJIS[game]:   # the in-place Shift-JIS slots: 16 bytes each, cut out of the kept spans
                keep = [x for a, b in keep for x in ((a, min(b, s)), (max(a, s + 16), b)) if x[0] < x[1]]
            if any(o[a:b] != n[a:b] for a, b in keep):
                bad.append(f"{p}: bytes changed outside the save-dialog region, its pointer table and the new-data title")
            for w in range(t0, t1, 4):
                v = int.from_bytes(n[w:w + 4], "little") + 0x80
                if not (r0 <= v < r1 and n[v - 1] == 0):
                    bad.append(f"{p}: table word {w:#x} points at {v:#x}, not a string start in the region")
            continue
        om, nm = dict(kpd.walk(orig_b[p])), dict(kpd.walk(new_b[p]))
        if list(om) != list(nm):
            bad.append(f"{p}: member list differs: {sorted(set(om) ^ set(nm))}")
        for m in om:
            if m in nm and om[m] != nm[m] and want[p].get(m) != nm[m]:
                bad.append(f"{p}: {m} changed, but not to the bytes build.edits() writes there")
    return bad


if __name__ == "__main__":
    iso = Path(sys.argv[1]) if len(sys.argv) > 1 else build.ROOT / "build" / "goku_en.iso"
    problems = check(iso)
    print("\n".join(problems) or f"diffcheck ok: {iso.name} writes only the text, the font and the PRX save strings")
    sys.exit(bool(problems))
