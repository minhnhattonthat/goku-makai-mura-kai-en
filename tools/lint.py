"""lint.py: width and line budgets of every inserted line, per box (docs/re/boxes.md), in the variable-width font's px.

Usage: lint.py [-v]   exit 1 on any error; -v lists the warnings too
Errors: a translated row (status done/recheck) over its box, or with control codes that differ from the jp.
Warnings: an official or inherited row over budget (the USA text, laid out for the 12 px fixed font; check it in game).
Rows still untranslated are counted, not failed, until phase 7.
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


def budget(name):
    return BOX.get(name) or (SUB if name.startswith("mv") else None)


def run():
    """(errors, warnings, untranslated count) as lists of strings / an int."""
    docs = script.load()
    bft = build.font_files()["font/jfont_00.bft"]
    t = bms.load_tbl()
    errors, warnings, todo = [], [], 0
    for game, files in docs.items():
        for name, doc in files.items():
            for r in doc["strings"]:
                if r["status"] in ("empty", "keep"):
                    continue
                text = script.en_text(r, docs)
                # translators set `done`; a jp already in English (credit names, ０－０) is not untranslated
                if r["status"] == "new" or (text == r["jp"] and re.search(script.JP_CHAR, text)):
                    todo += 1
                    continue
                own = r["status"] not in ("official", "inherit")
                if own and Counter(CODES.findall(text)) != Counter(CODES.findall(r["jp"])):
                    errors.append(f"{game}/{r['id']}: control codes differ from the jp")
                if name == "prx":
                    if len(text.encode("utf-8")) > r["max"]:
                        errors.append(f"{game}/{r['id']}: {len(text.encode())} bytes, slot holds {r['max']}")
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
    return errors, warnings, todo


if __name__ == "__main__":
    errors, warnings, todo = run()
    print("\n".join(errors + (warnings if "-v" in sys.argv else [])))
    print(f"lint: {len(errors)} errors, {len(warnings)} warnings (official text over budget), {todo} rows untranslated")
    sys.exit(bool(errors))
