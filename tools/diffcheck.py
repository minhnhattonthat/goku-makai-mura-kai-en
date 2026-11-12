"""diffcheck.py: the build writes only where it should (the romdiff check, per layer of the disc).

Usage: diffcheck.py [BUILT_ISO]   (default build/goku_en.iso); exit 1 on any problem
- ISO: every changed byte is a changed file's data (old or new extent), its directory record (LBA, size) or the volume
  size in the PVD; no file was added or dropped; the files that differ are exactly the ones build.edits() replaces.
  No Japanese UTF-8 (3+ characters) is left in a built PRX.
- Archives: the same member list as the original; members that differ are only .bms files and the font (build.FONT).
- PRX: bytes differ only in the save-dialog region (script.PRX) and its pointer table (script.PRX_PTRS); every table
  word points at a string start in the region.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build
import iso9660
import kpd
import script

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
        end = fa.seek(0, 2)
        fa.seek(0)
        at = 0
        while at < end:
            x, y = fa.read(CHUNK), fb.read(CHUNK)
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
        if p.endswith(".PRX"):
            game = next(g for g, n in script.GAMES.items() if p.endswith("/" + n + ".PRX"))
            (r0, r1), (t0, t1) = script.PRX[game], script.PRX_PTRS[game]
            o, n = orig_b[p], new_b[p]
            if len(o) != len(n):
                bad.append(f"{p}: size changed")
            bad += [f"{p}: Japanese UTF-8 left at {m.start():#x}" for m in script.JP_UTF8.finditer(n)]
            if o[:r0] != n[:r0] or o[r1:t0] != n[r1:t0] or o[t1:] != n[t1:]:
                bad.append(f"{p}: bytes changed outside the save-dialog region and its pointer table")
            for w in range(t0, t1, 4):
                v = int.from_bytes(n[w:w + 4], "little") + 0x80
                if r0 < v < r1 and n[v - 1] != 0:
                    bad.append(f"{p}: table word {w:#x} points mid-string at {v:#x}")
            continue
        om, nm = dict(kpd.walk(orig_b[p])), dict(kpd.walk(new_b[p]))
        if list(om) != list(nm):
            bad.append(f"{p}: member list differs: {sorted(set(om) ^ set(nm))}")
        for m in om:
            if m in nm and om[m] != nm[m] and not (m.endswith(".bms") or m in build.FONT):
                bad.append(f"{p}: {m} changed, but the build only writes .bms and the font")
    return bad


if __name__ == "__main__":
    iso = Path(sys.argv[1]) if len(sys.argv) > 1 else build.ROOT / "build" / "goku_en.iso"
    problems = check(iso)
    print("\n".join(problems) or f"diffcheck ok: {iso.name} writes only the text, the font and the PRX save strings")
    sys.exit(bool(problems))
