"""pairs.py: a reviewer's pairs file (docs/reviewer-brief.md): rows of the given statuses, with +-2 neighbours of the same file.

Usage: pairs.py OUT.txt [STATUS ...]   (default: done)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import script

if len(sys.argv) < 2 or sys.argv[1].startswith("-"):   # `--help` once became the output file name
    sys.exit(__doc__)
docs = script.load()
want = set(sys.argv[2:] or ["done"])
out = []
for game, files in docs.items():
    for name, doc in files.items():
        rows = doc["strings"]
        for i, r in enumerate(rows):
            if r["status"] not in want:
                continue
            out.append(f"\n### {game}/{name}")
            for j in range(max(0, i - 2), min(len(rows), i + 3)):
                x = rows[j]
                if x["status"] == "empty":
                    continue
                mark = ">>" if j == i else "  "
                lim = f" (max {x['max']} bytes)" if "max" in x else ""
                out.append(f"{mark} {x['id']}{lim} [{x['status']}] | JP: {x['jp']!r}\n   EN: {script.en_text(x, docs)!r}")
                if j == i and x.get("notes"):
                    out.append(f"   NOTE: {x['notes']}")
Path(sys.argv[1]).write_text("\n".join(out) + "\n", encoding="utf-8")
