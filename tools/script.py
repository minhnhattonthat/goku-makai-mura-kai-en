"""script.py: the game text in script/, one JSON file per message file.

Usage: script.py dump      write or refresh script/<game>/<name>.json from the dumps in rom/ (never drops an `en`)
       script.py check     roundtrip + coverage against the dumps; exit 1 on any problem (tests/test_script.py runs it too)
       script.py stats     counts per status

Games: `re` = Kai (USRDIR/REGOKUMAKAI), `go` = the original (USRDIR/GOKUMAKAI). Sources:
- every .bms in each game's datapack.kpd (docs/re/text.md): id `<stem>:<index>`;
- the UTF-8 save-dialog strings in <game>.PRX (prx.json): id `prx:<file offset>`, `max` = bytes the slot holds before its NUL.
Entry fields: id, jp, en, status, plus `us` (official English from the USA disc, D10: same file and index, original game only)
and `same` (a Kai entry whose jp equals an original-game entry: it takes that entry's en on insert).
Status: official (en = us), inherit (en comes from `same`), new (needs translating), empty (an empty string; insert as is).
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bms
import build
import kpd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "script"
US_ISO = ROOT / "rom" / "Ultimate Ghosts 'n Goblins (USA).iso"
GAMES = {"re": "REGOKUMAKAI", "go": "GOKUMAKAI"}
# save-dialog string region per PRX: [start, end) file offsets (verified by dumping the NUL-separated strings, 2026-11-12)
PRX = {"re": (0x3495A0, 0x349904), "go": (0x349B30, 0x349E80)}
JP_CHAR = r"[぀-ヿ一-鿿]"  # kana and kanji (the USA text keeps fullwidth spaces, which are fine)
# 3+ kana/kanji in a row: two-char runs turn up in MIPS code by chance (go.PRX 0x497fa)
JP_UTF8 = re.compile(rb"(?:[\xe3-\xe9][\x80-\xbf]{2}){3,}")


def archive(game):
    return build.USR + GAMES[game] + "/datapack.kpd"


def bms_files(iso, path):
    d = build.read_files(iso, [path])[path]
    return {p: b for p, b in kpd.walk(d) if p.endswith(".bms")}


def prx_bytes(game):
    p = build.USR + GAMES[game] + "/" + GAMES[game] + ".PRX"
    return build.read_files(build.ROM, [p])[p]


def prx_strings(d, start, end):
    """[(offset, raw bytes, slot bytes before the next string)] for every NUL-separated string in the region."""
    out = [(m.start() + start, m.group()) for m in re.finditer(rb"[^\0]+", d[start:end])]
    return [(o, s, (out[i + 1][0] if i + 1 < len(out) else end) - o - 1) for i, (o, s) in enumerate(out)]


def extract():
    """{game: {name: {"path", "strings": [raw bytes], ...}}} straight from the dumps."""
    t = bms.load_tbl()
    us = {Path(p).stem: bms.parse(b) for p, b in bms_files(US_ISO, "/PSP_GAME/USRDIR/datapack.kpd").items()}
    res = {}
    for game in GAMES:
        files = {}
        for path, b in sorted(bms_files(build.ROM, archive(game)).items()):
            raw = bms.parse(b)
            rows = []
            for i, s in enumerate(raw):
                row = {"id": f"{Path(path).stem}:{i}", "jp": bms.decode(s, t)}
                u = us.get(Path(path).stem) if game == "go" else None
                if u is not None and i < len(u):
                    row["us"] = bms.decode(u[i], t)
                rows.append(row)
            files[Path(path).stem] = {"archive": archive(game), "path": path, "strings": rows, "raw": raw, "file": b}
        d = prx_bytes(game)
        rows = []
        for o, s, room in prx_strings(d, *PRX[game]):
            if s.isascii():
                continue  # format strings and the English mode names stay as they are
            rows.append({"id": f"prx:{o:#x}", "jp": s.decode("utf-8"), "max": room})
        files["prx"] = {"archive": build.USR + GAMES[game] + "/" + GAMES[game] + ".PRX", "strings": rows}
        res[game] = files
    return res


def link(res):
    """Fill status, en and same on fresh rows."""
    by_jp = {}
    for name, f in res["go"].items():
        for r in f["strings"]:
            by_jp.setdefault(r["jp"], []).append(f"go/{r['id']}")
    for game, files in res.items():
        for name, f in files.items():
            for r in f["strings"]:
                if r["jp"] == "":
                    r["status"] = "empty"
                elif "us" in r and re.search(JP_CHAR, r["us"]):
                    r["status"] = "new"  # the USA release left part of it Japanese (a03:142): translate that part
                    r["notes"] = "USA text keeps a Japanese line; translate it in the USA style"
                elif "us" in r:
                    r["status"] = "official"
                elif game == "re" and r["jp"] in by_jp:
                    # before `keep`: English-only Kai rows still take the USA spelling (Red Arimmar -> Red Devil)
                    cands = by_jp[r["jp"]]
                    r["same"] = f"go/{r['id']}" if f"go/{r['id']}" in cands else cands[0]
                    r["status"] = "inherit"
                elif not re.search(JP_CHAR, r["jp"]):
                    r["status"], r["en"] = "keep", r["jp"]  # digits and marks only (Kai a02:24-34): insert as is
                else:
                    r["status"] = "new"


def order(r):
    keys = ["id", "jp", "us", "same", "max", "en", "status", "notes"]
    return {k: r[k] for k in keys if k in r}


def merge(r, o):
    """Fresh row r takes the work in its old row o; True when it kept an en."""
    if o and o.get("notes"):
        r["notes"] = o["notes"]
    if o and o.get("en") and o["en"] != o.get("us", ""):
        # an en still equal to the USA text is only the prefill, so it refreshes; flag work whose source text changed
        r["en"], r["status"] = o["en"], ("recheck" if o["jp"] != r["jp"] else o["status"])
        return True
    r.setdefault("en", r.get("us", ""))  # `keep` rows already carry en = jp
    return False


def dump():
    res = extract()
    link(res)
    n_new = n_kept = 0
    for game, files in res.items():
        for name, f in files.items():
            path = OUT / game / f"{name}.json"
            old = {}
            if path.exists():
                old = {r["id"]: r for r in json.loads(path.read_text(encoding="utf-8"))["strings"]}
            rows = []
            for r in f["strings"]:
                kept = merge(r, old.get(r["id"]))
                n_kept += kept
                n_new += not kept
                rows.append(order(r))
            doc = {"game": game, "archive": f["archive"]}
            if "path" in f:
                doc["path"] = f["path"]
            doc["strings"] = rows
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{n_new} rows written fresh, {n_kept} kept their en")


def load():
    """{game: {name: doc}} from script/."""
    return {g: {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((OUT / g).glob("*.json"))} for g in GAMES}


def check():
    """Problems as strings; [] = roundtrip exact and every string covered."""
    t = bms.load_tbl()
    res = extract()
    have = load()
    bad = []
    for game, files in res.items():
        names = set(files)
        if set(have[game]) != names:
            bad.append(f"{game}: script/ files {sorted(set(have[game]) ^ names)} differ from the dump")
        for name, f in files.items():
            if "file" in f:
                # coverage: the offset table and the strings are the whole file, so writing them back gives the file
                if bms.build(f["raw"]) != f["file"]:
                    bad.append(f"{game}/{name}: bms.build(parse()) differs from the file")
                for i, s in enumerate(f["raw"]):
                    x = bms.decode(s, t)
                    if bms.encode(x, t) != s:
                        bad.append(f"{game}/{name}:{i}: encode(decode()) differs")
                    if re.search(r"\[[0-9A-F]{2}\]", x):
                        bad.append(f"{game}/{name}:{i}: undecoded bytes {x!r}")
            got = {r["id"]: r for r in have[game].get(name, {}).get("strings", [])}
            for r in f["strings"]:
                g = got.get(r["id"])
                if g is None or g["jp"] != r["jp"]:
                    bad.append(f"{game}/{r['id']}: script/ jp is missing or stale (run script.py dump)")
            if len(got) != len(f["strings"]):
                bad.append(f"{game}/{name}: {len(got)} rows in script/, {len(f['strings'])} in the dump")
        # PRX: no Japanese UTF-8 outside the save-dialog region, every string in it encodes back to its slot
        d = prx_bytes(game)
        a, b = PRX[game]
        for m in JP_UTF8.finditer(d):
            if not a <= m.start() < b:
                bad.append(f"{game}.PRX: Japanese UTF-8 outside the region at {m.start():#x}")
        for r in files["prx"]["strings"]:
            o = int(r["id"][4:], 16)
            s = r["jp"].encode("utf-8")
            if d[o:o + len(s) + 1] != s + b"\0" or len(s) > r["max"]:
                bad.append(f"{game}/{r['id']}: does not roundtrip")
    return bad


def stats():
    from collections import Counter
    for game, files in load().items():
        c = Counter(r["status"] for f in files.values() for r in f["strings"])
        chars = sum(len(r["jp"]) for f in files.values() for r in f["strings"] if r["status"] == "new")
        print(game, dict(c), f"new jp chars: {chars}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "dump":
        dump()
    elif cmd == "stats":
        stats()
    else:
        problems = check()
        print("\n".join(problems) or "script ok: roundtrip exact, every string covered")
        sys.exit(bool(problems))
