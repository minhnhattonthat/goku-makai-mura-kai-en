"""lint.py: width and line budgets of every inserted line, per box (docs/re/boxes.md), in the variable-width font's px.

Usage: lint.py [-v]   exit 1 on any error; -v lists the warnings too
Errors, on a translated row (status done/recheck): over its box; control codes, printf specifiers (prx) or leading and
trailing blanks that differ from the jp; a glossary term's JP without its EN, or an "Avoid" spelling (glossary.md);
a stub last line (under 6 characters after a longer line); an ordinal suffix glued to a variable (%dth);
a prx or sfo row that is not ASCII, or a prx row that finds no room in the PRX region.
Any row still untranslated is an error too, unless its id is in script/keep_jp.txt (`<game>/<id> reason` per line).
Warnings: an official or inherited row over budget (the USA text, laid out for the 12 px fixed font; check it in game).
"""
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bms
import build
import script
import vwf

HELP = [412, 412]          # 2 lines; the engine wraps a longer line at 412-420 px (ruler build, re/go)
ICONS = [412, 300]         # line 2 shares the row with the circle/cross button icons (from x 335)
SUB = [440, 440]           # block-centred subtitles; 20 px margin each side of the 480 px screen
BOX = {
    "a02": HELP, "a04": HELP, "a10": ICONS, "a30": ICONS,
    "s0506": HELP, "s0507": HELP, "s0600": HELP, "s0700": HELP, "s0800": HELP,
    "memstick": [440] * 15,    # block-centred prompt, no box, blank lines position it; go:11 draws 15 rows (marker shot)
    "a03": [182] * 8,          # sub-screen detail pane: wraps at 182-189 px (name and description)
}
CODES = re.compile(r"\{[^}]*\}")
PRINTF = re.compile(r"%[-+ #0-9.]*[a-zA-Z]")
ROOT = Path(__file__).resolve().parents[1]


def budget(name):
    return BOX.get(name) or (SUB if name.startswith("mv") else None)


def glossary():
    """[(jp forms, en forms, avoid)] from glossary.md's tables; only rows whose JP cells are plain kana/kanji terms."""
    out = []
    for line in (ROOT / "glossary.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not line.startswith("|") or len(cells) != 5:
            continue
        jp = cells[0].split(" / ")
        if not all(re.fullmatch(script.JP_CHAR + "+", j) for j in jp):
            continue   # headers, ranges like `1-1 魔の森 ..`, patterns like 第Nの魔界門
        en = [re.sub(r"\(.*?\)|^the |\"", "", e).strip().lower() for e in cells[1].split(" / ")]
        out.append((jp, en, [a.strip().lower() for a in cells[4].split(",") if a.strip()]))
    return sorted(out, key=lambda t: -max(map(len, t[0])))


def keep_jp():
    f = ROOT / "script" / "keep_jp.txt"
    return {l.split()[0] for l in f.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")} if f.exists() else set()


def blanks(s):
    return re.match(r"[ 　\n]*", s).group(), re.search(r"[ 　\n]*$", s).group()


def run():
    """(errors, warnings, untranslated count) as lists of strings / an int."""
    docs = script.load()
    bft = build.font_files()["font/jfont_00.bft"]
    t = bms.load_tbl()
    errors, warnings, todo = [], [], 0
    terms, waived = glossary(), keep_jp()
    for game, files in docs.items():
        for name, doc in files.items():
            for r in doc["strings"]:
                if r["status"] in ("empty", "keep"):
                    continue
                text = script.en_text(r, docs)
                # translators set `done`; a jp already in English (credit names) is not untranslated
                if r["status"] == "new" or (text == r["jp"] and re.search(script.JP_CHAR, text)):
                    if f"{game}/{r['id']}" not in waived:
                        todo += 1
                        errors.append(f"{game}/{r['id']}: untranslated (not in script/keep_jp.txt)")
                    continue
                own = r["status"] not in ("official", "inherit")
                if own:
                    if Counter(CODES.findall(text)) != Counter(CODES.findall(r["jp"])):
                        errors.append(f"{game}/{r['id']}: control codes differ from the jp")
                    if [b.count("\n") for b in blanks(text)] != [b.count("\n") for b in blanks(r["jp"])]:
                        errors.append(f"{game}/{r['id']}: leading or trailing line breaks differ from the jp")
                    low = re.sub(r"\s+", " ", CODES.sub("", text)).lower()   # a name may break across lines
                    left = r["jp"]
                    for jp, en, avoid in terms:   # longest first: 最強の魔力 hides its 魔力
                        if any(j in left for j in jp) and not any(e in low for e in en):
                            errors.append(f"{game}/{r['id']}: {jp[0]} without its glossary EN ({' / '.join(en)})")
                        for j in jp:
                            left = left.replace(j, "\0")
                        errors += [f"{game}/{r['id']}: glossary Avoid spelling '{a}'" for a in avoid if a in low]
                    for page in text.split("{06}"):
                        lines = [CODES.sub("", l).strip() for l in page.strip("\n").split("\n")]
                        if len(lines) > 1 and 0 < len(lines[-1]) < 6 and len(lines[-2]) >= 6:
                            errors.append(f"{game}/{r['id']}: stub last line '{lines[-1]}'")
                if re.search(r"(%[-+ #0-9.]*[a-zA-Z]|\{[^}]*\})(st|nd|rd|th)\b", text):
                    errors.append(f"{game}/{r['id']}: ordinal suffix glued to a variable (1th): rephrase")
                if name in ("prx", "sfo"):
                    if own and Counter(PRINTF.findall(text)) != Counter(PRINTF.findall(r["jp"])):
                        errors.append(f"{game}/{r['id']}: printf specifiers differ from the jp")
                    if not text.isascii():
                        errors.append(f"{game}/{r['id']}: not ASCII")
                    if name == "sfo" and len(text.encode()) > r["max"]:
                        errors.append(f"{game}/{r['id']}: {len(text.encode())} bytes > {r['max']}")
                    continue
                if re.search(script.JP_CHAR, text) and own:
                    errors.append(f"{game}/{r['id']}: Japanese left in the en")
                try:
                    bms.encode(text, t)
                except ValueError as e:   # e.g. [ ] { } < > @ _ ~ $: not in the font
                    errors.append(f"{game}/{r['id']}: {e}")
                    continue
                bad = []
                for p, page in enumerate(text.split("{06}")):   # 06: page break (a03 descriptions)
                    lim = budget(name)
                    widths = vwf.line_widths(page, bft, t)
                    at = f"page {p + 1} " if "{06}" in text else ""
                    bad += [f"{at}line {i + 1} {w}px > {lim[i]}" for i, w in enumerate(widths) if i < len(lim) and w > lim[i]]
                    if len(widths) > len(lim):
                        bad.append(f"{at}{len(widths)} lines > {len(lim)}")
                if bad:
                    (errors if own else warnings).append(f"{game}/{r['id']}: " + ", ".join(bad))
        rows = files["prx"]["strings"]
        try:
            script.prx_patch(game, rows, [(r["jp"] if r["status"] in ("empty", "keep") else script.en_text(r, docs)).encode()
                                          for r in rows])
        except ValueError as e:
            errors.append(str(e))
    return errors, warnings, todo


if __name__ == "__main__":
    errors, warnings, todo = run()
    print("\n".join(errors + (warnings if "-v" in sys.argv else [])))
    print(f"lint: {len(errors)} errors, {len(warnings)} warnings (official text over budget), {todo} rows untranslated")
    sys.exit(bool(errors))
