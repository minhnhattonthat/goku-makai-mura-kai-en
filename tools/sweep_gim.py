"""sweep_gim.py ROOT... : decode every unique .gim (except the font) into work/sweep/*.png for the graphics survey.

Prints every file it could not decode and why, so nothing is dropped silently.
"""
import collections
import hashlib
import os
import sys

import gim


def main(roots):
    os.makedirs("work/sweep", exist_ok=True)
    seen, sizes, failed = {}, collections.Counter(), []
    for root in roots:
        for dp, _, fs in os.walk(root):
            for f in fs:
                if not f.endswith(".gim") or f.startswith("jfont"):
                    continue
                p = os.path.join(dp, f)
                b = open(p, "rb").read()
                h = hashlib.md5(b).hexdigest()
                if h in seen:
                    continue
                seen[h] = p
                try:
                    im = gim.parse(b)[0]
                    w, hh, rows = gim.to_rgba(b, im)
                    sizes[(w, hh)] += 1
                    gim.save_png(f"work/sweep/{f[:-4]}_{h[:6]}.png", w, hh, rows)
                except Exception as e:
                    failed.append((p, repr(e)))
    print(len(seen), "unique,", len(failed), "failed", sizes.most_common(10))
    for p, e in failed:
        print("FAIL", p, e)


if __name__ == "__main__":
    main(sys.argv[1:])
