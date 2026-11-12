"""script.py: the game text in script/, one JSON file per message file.

Usage: script.py dump      write or refresh script/<game>/<name>.json from the dumps in rom/ (never drops an `en`)
       script.py check     roundtrip + coverage against the dumps; exit 1 on any problem (tests/test_script.py runs it too)
       script.py stats     counts per status

Games: `re` = Kai (USRDIR/REGOKUMAKAI), `go` = the original (USRDIR/GOKUMAKAI). Sources:
- every .bms in each game's datapack.kpd (docs/re/text.md): id `<stem>:<index>`;
- the UTF-8 save-dialog strings in <game>.PRX (prx.json), plus its Shift-JIS new-data title (PRX_SJIS): id
  `prx:<file offset>`, `max` = bytes the slot holds before its NUL;
- the disc's PARAM.SFO TITLE (re/sfo.json, id `sfo:TITLE`, `max` UTF-8 bytes).
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
import sfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "script"
US_ISO = ROOT / "rom" / "Ultimate Ghosts 'n Goblins (USA).iso"
GAMES = {"re": "REGOKUMAKAI", "go": "GOKUMAKAI"}
# save-dialog string region per PRX: [start, end) file offsets (verified by dumping the NUL-separated strings, 2026-11-12)
PRX = {"re": (0x3495A0, 0x349904), "go": (0x349B30, 0x349E80)}
JP_CHAR = r"[぀-ヿ一-鿿]"  # kana and kanji (the USA text keeps fullwidth spaces, which are fine)
# 3+ kana/kanji in a row: two-char runs turn up in MIPS code by chance (go.PRX 0x497fa)
JP_UTF8 = re.compile(rb"(?:[\xe3-\xe9][\x80-\xbf]{2}){3,}")
# Shift-JIS strings in the PRX outside the region: the save utility's new-data title 新規作成データ (loaded by lui/addiu at
# re 0x41a98, go 0x42eb0, after the new-data icon paths). No pointer table: written in place, never moved. [file offsets]
PRX_SJIS = {"re": [0x349AD0], "go": [0x34A070]}
SJIS_STR = re.compile(rb"(?<=\0)(?:[\x81-\x9f\xe0-\xfc][\x40-\x7e\x80-\xfc]|[\x20-\x7e])+\0")   # no halfwidth kana
SFO = "/PSP_GAME/PARAM.SFO"   # the disc's XMB title (TITLE, UTF-8): row sfo:TITLE in script/re/sfo.json


def sjis_runs(d):
    """File offsets of the Shift-JIS strings in a PRX: NUL-bounded, 4-aligned, 3+ kana/kanji, not valid UTF-8 (the
    region's strings are). Code and float data match the byte pattern too, but not all of this (2026-11-12: one hit per
    PRX, the PRX_SJIS string)."""
    out = []
    for m in SJIS_STR.finditer(d):
        s = m.group()[:-1]
        if m.start() % 4:
            continue
        try:
            t = s.decode("cp932")
        except UnicodeDecodeError:
            continue
        try:
            s.decode("utf-8")
            continue
        except UnicodeDecodeError:
            pass
        if len(re.findall(JP_CHAR, t)) >= 3:
            out.append(m.start())
    return out


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
        for o in PRX_SJIS[game]:
            s = d[o:d.index(b"\0", o)]
            rows.append({"id": f"prx:{o:#x}", "jp": s.decode("cp932"), "max": len(s) + len(re.match(rb"\0*", d[o + len(s):]).group()) - 1})
        files["prx"] = {"archive": build.USR + GAMES[game] + "/" + GAMES[game] + ".PRX", "strings": rows}
        if game == "re":
            _, _, mx, _, title = sfo.read(build.read_files(build.ROM, [SFO])[SFO])["TITLE"]
            files["sfo"] = {"archive": SFO, "strings": [{"id": "sfo:TITLE", "jp": title, "max": mx - 1}]}
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
        if sjis_runs(d) != PRX_SJIS[game]:
            bad.append(f"{game}.PRX: Shift-JIS strings at {[hex(o) for o in sjis_runs(d)]} != PRX_SJIS")
        for r in files["prx"]["strings"]:
            o = int(r["id"][4:], 16)
            s = r["jp"].encode(prx_enc(game, o))
            if d[o:o + len(s) + 1] != s + b"\0" or len(s) > r["max"]:
                bad.append(f"{game}/{r['id']}: does not roundtrip")
    return bad


FILLER = "The quick brown fox jumps over the lazy dog. "
TOKENS = re.compile(r"(\{[^}]*\}|\n)")


def marker(r, fill=None):
    """`(id) filler` in place of the text, keeping the line breaks and control codes of the jp. Each text run becomes
    filler 1.5x its JP length (an 18 px JP cell against a 12 px ASCII cell), the first run starts with the id.
    fill: every run is this string instead (RULER, to read each box's width off a shot; TORTURE, every glyph)."""
    out, first = [], True
    for part in TOKENS.split(r["jp"]):
        if not part or TOKENS.fullmatch(part) or not part.strip(" 　"):
            out.append(part)
            continue
        head = f"({r['id']}) " if first else ""  # the font has no [ ]
        first = False
        core = part.strip(" 　")
        lead, tail = part[:part.index(core)], part[part.index(core) + len(core):]   # the gap between choices stays
        n = max(len(head), round(len(core) * 1.5))
        out.append(lead + (head + fill if fill else (head + FILLER * (n // len(FILLER) + 1))[:n]) + tail)
    return "".join(out)


# width gate: the last character still drawn tells the box's budget (vwf.line_widths of the prefix up to it)
RULER = "".join(c + "123456789" for c in "ABCDEFGHJK")
# every ASCII character the font has (no [ ] { } < > @ ^ _ ` \ | ~ $), double spaces, the ™ and ★ cells
TORTURE = "AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz 0123456789  !\"#%&'()*+,-./:;=?™★"


def en_text(r, docs):
    """The text a row inserts: its en, an `inherit` row its source row's en; an untranslated row keeps its jp."""
    if r["status"] == "inherit":
        game, rid = r["same"].split("/")
        src = next(x for x in docs[game][rid.split(":")[0]]["strings"] if x["id"] == rid)
        return en_text(src, docs)
    return r["en"] or r["jp"]


def insert(marker_build=None):
    """{iso path: {archive path: bytes}} for the .bms files, {iso path: bytes} for the PRXes (strings in place, NUL padded).
    marker_build: None (the translation), "id" (marker build), "ruler" or "torture" (width gate)."""
    t = bms.load_tbl()
    docs = load()
    fill = {"ruler": RULER, "torture": TORTURE}.get(marker_build)
    out = {}
    for game, files in docs.items():
        for name, doc in files.items():
            rows = doc["strings"]
            text = [r["jp"] if r["status"] in ("empty", "keep") else
                    marker(r, fill) if marker_build else en_text(r, docs) for r in rows]
            if name == "sfo":
                out[SFO] = sfo.set_str(build.read_files(build.ROM, [SFO])[SFO], "TITLE", text[0])
                continue
            if name != "prx":
                out.setdefault(doc["archive"], {})[doc["path"]] = bms.build([bms.encode(s, t) for s in text])
                continue
            out[doc["archive"]] = prx_patch(game, rows, [s.encode("utf-8")[:r["max"]] if marker_build else s.encode("utf-8")
                                                         for r, s in zip(rows, text)])
    return out


# the u32 pointer table that holds every save-dialog string's address (value + 0x80 = file offset; one R_MIPS_32 reloc
# each, so a new value relocates the same way). Every row has its pointers here and nowhere else: no other relocated
# word or lui/addiu pair points into the region (tests/test_checks.py test_prx_region_read_only_through_the_table).
PRX_PTRS = {"re": (0x351488, 0x351514), "go": (0x351988, 0x351A14)}


def prx_pointers(d, game, o):
    a, b = PRX_PTRS[game]
    return [p for p in range(a, b, 4) if int.from_bytes(d[p:p + 4], "little") == o - 0x80]


def prx_enc(game, o):
    """The encoding of the PRX string at file offset o: UTF-8 in the save-dialog region, Shift-JIS (PRX_SJIS) outside."""
    return "utf-8" if PRX[game][0] <= o < PRX[game][1] else "cp932"


def prx_patch(game, rows, texts):
    """The PRX with each row's string (bytes, no NUL) written. A string that fits its own slot stays there; a longer one
    moves, 4-aligned like the compiler's, into the free tail of another slot and its table pointers are rewritten.
    ValueError when one finds no room (a PRX_SJIS row has no table pointer, so it must fit its own slot)."""
    d = bytearray(prx_bytes(game))
    slots = []
    for r, s in zip(rows, texts):
        o = int(r["id"][4:], 16)
        old = r["jp"].encode(prx_enc(game, o))
        assert d[o:o + len(old) + 1] == old + b"\0", f"{game}/{r['id']}: slot does not hold its jp"
        in_region = prx_enc(game, o) == "utf-8"
        ptrs = prx_pointers(d, game, o) if in_region else []
        assert ptrs or not in_region, f"{game}/{r['id']}: no pointer in the table"
        if not in_region and len(s) > r["max"]:
            raise ValueError(f"{game}/{r['id']}: {len(s)} bytes > its {r['max']}-byte slot (no pointer to move it by)")
        d[o:o + r["max"] + 1] = bytes(r["max"] + 1)
        slots.append((o, r["max"] + 1, s, ptrs, r["id"], in_region))
    free = []   # [start, end) bytes no string uses, inside the region only
    moved = [x for x in slots if len(x[2]) + 1 > x[1]]
    for o, room, s, _, _, in_region in slots:
        if len(s) + 1 <= room:
            d[o:o + len(s)] = s
            if in_region:
                free.append([o + len(s) + 1, o + room])
        else:
            free.append([o, o + room])
    up = lambda x: (x + 3) & ~3
    for _, _, s, ptrs, rid, _ in sorted(moved, key=lambda x: -len(x[2])):
        f = next((f for f in sorted(free, key=lambda f: f[1] - f[0]) if f[1] - up(f[0]) >= len(s) + 1), None)
        if f is None:
            raise ValueError(f"{game}/{rid}: {len(s)} bytes, no free slot space left in the PRX region")
        at = up(f[0])
        d[at:at + len(s)] = s
        for p in ptrs:
            d[p:p + 4] = (at - 0x80).to_bytes(4, "little")
        f[0] = at + len(s) + 1
    return bytes(d)


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
