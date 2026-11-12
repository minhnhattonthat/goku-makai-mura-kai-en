"""chapters.py: story-pass chapter files (references/translation.md §Review), one per game, in story order.

Usage: chapters.py OUTDIR   (writes OUTDIR/<game>_story.txt; then qa_gate.py init MANIFEST OUTDIR --glob "*.txt")
Order: opening movie, the other movies, stage messages (s05..s08), the ending movies. No speaker field in the data.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import script

ORDER = ["mv00", "mv01", "mv02", "mv03", "s0506", "s0507", "s0600", "s0700", "s0800", "mv04", "mv05", "mv06"]

if len(sys.argv) != 2 or sys.argv[1].startswith("-"):
    sys.exit(__doc__)
out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
docs = script.load()
for game, files in docs.items():
    lines = [f"# {game}: story text in play order ({', '.join(ORDER)})"]
    for name in ORDER:
        lines.append(f"\n## {name}")
        for r in files[name]["strings"]:
            if r["status"] != "empty":
                lines.append(f">> {name}/{r['id']} | - | {r['jp']!r}\n   EN: {script.en_text(r, docs)!r}")
    (out / f"{game}_story.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
