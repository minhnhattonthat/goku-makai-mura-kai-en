"""gfxshow.py: PNGs with alpha on a dark backdrop, stacked and zoomed, to read white lettering (sheet.py drops alpha).

Usage: gfxshow.py OUT.png IN.png [IN.png ...] [--zoom 3]
"""
import sys

from PIL import Image

a = sys.argv[1:]
zoom = 3
if "--zoom" in a:
    i = a.index("--zoom")
    zoom = int(a[i + 1])
    del a[i:i + 2]
out, ims = a[0], [Image.open(p).convert("RGBA") for p in a[1:]]
W, H = max(i.width for i in ims), sum(i.height + 4 for i in ims)
c = Image.new("RGBA", (W, H), (70, 70, 110, 255))
y = 0
for im in ims:
    bg = Image.new("RGBA", im.size, (70, 70, 110, 255))
    bg.alpha_composite(im)
    c.paste(bg, (0, y))
    y += im.height + 4
c.resize((W * zoom, H * zoom), Image.NEAREST).save(out)
print(out)
