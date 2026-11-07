"""gimsheet.py OUT.png DIR|PNG...: labelled contact sheet of texture PNGs on a dark background, deduped by pixels, paged.

Shelf-packs at native size (--zoom N to enlarge) and writes OUT.png, OUT_2.png... under --width/--height. Prints the pages.
"""
import argparse
import glob
import hashlib
import os

from PIL import Image, ImageDraw


def main():
    a = argparse.ArgumentParser()
    a.add_argument("out")
    a.add_argument("src", nargs="+")
    a.add_argument("--zoom", type=int, default=1)
    a.add_argument("--width", type=int, default=1600)
    a.add_argument("--height", type=int, default=1200)
    o = a.parse_args()
    files = []
    for s in o.src:
        files += sorted(glob.glob(os.path.join(s, "**", "*.png"), recursive=True)) if os.path.isdir(s) else sorted(glob.glob(s))
    seen, cells = set(), []
    for f in files:
        im = Image.open(f).convert("RGBA")
        h = hashlib.md5(im.tobytes()).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        bg = Image.new("RGBA", im.size, (70, 70, 110, 255))
        bg.alpha_composite(im)
        cells.append((os.path.basename(os.path.dirname(f)) + "/" + os.path.basename(f)[:-4], bg.convert("RGB").resize((im.width * o.zoom, im.height * o.zoom), Image.NEAREST)))
    pages, page, x, y, rh = [], [], 0, 0, 0
    for label, c in cells:
        w, h = max(c.width, len(label) * 6 + 2) + 6, c.height + 14
        if x + w > o.width and x:
            x, y, rh = 0, y + rh, 0
        if y + h > o.height and page:
            pages.append(page)
            page, x, y, rh = [], 0, 0, 0
        page.append((x, y, label, c))
        x, rh = x + w, max(rh, h)
    if page:
        pages.append(page)
    stem = o.out[:-4]
    for i, p in enumerate(pages):
        W = max(x + max(c.width, len(l) * 6 + 2) + 6 for x, y, l, c in p)
        H = max(y + c.height + 14 for x, y, l, c in p)
        s = Image.new("RGB", (W, H), (20, 20, 20))
        d = ImageDraw.Draw(s)
        for x, y, l, c in p:
            d.text((x + 1, y), l, fill=(255, 255, 0))
            s.paste(c, (x, y + 12))
        name = o.out if i == 0 else f"{stem}_{i + 1}.png"
        s.save(name)
        print(name, s.size, len(p))


if __name__ == "__main__":
    main()
