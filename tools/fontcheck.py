"""fontcheck.py: check tbl/jp.tbl by eye: font sheet rows with the table character (mk_tbl.ROWS) drawn under each cell.

Usage: fontcheck.py [GIM] --sheet OUT.png [--rows 10-13] [--zoom 2]
Read every kanji row this way after changing ROWS (4 rows per sheet at zoom 2 are readable; zoom 4 for look-alikes).
Template matching against MS Gothic was tried and failed: the game font is bold with an outline, nearly every cell matched
a dense wrong kanji. The USA font (work/us/font) has the same cell layout, so the same table decodes the USA text.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gim
import mk_tbl

ROOT = Path(__file__).resolve().parents[1]
FONT = "C:/Windows/Fonts/msgothic.ttc"


def sheet_img(path):
    d = Path(path).read_bytes()
    w, h, rows = gim.to_rgba(d, gim.parse(d)[0])
    return Image.frombytes("RGBA", (w, h), b"".join(rows))


def cell(img, r, c):
    # brightness on black: alpha also covers the dark outline
    ce = img.crop((c * 18, r * 16, c * 18 + 18, r * 16 + 16))
    return Image.alpha_composite(Image.new("RGBA", ce.size, (0, 0, 0, 255)), ce).convert("L")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gim", nargs="?", default=ROOT / "work/re/font/jfont_00.gim")
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--rows", default="10-13")
    ap.add_argument("--zoom", type=int, default=2)
    a = ap.parse_args()
    img = sheet_img(a.gim)
    r0, r1 = map(int, a.rows.split("-"))
    z = a.zoom
    out = Image.new("RGB", (28 * 18 * z + 30, (r1 - r0 + 1) * 40 * z), (24, 24, 32))
    dr = ImageDraw.Draw(out)
    big, lab = ImageFont.truetype(FONT, 16 * z), ImageFont.truetype(FONT, 12)
    for r in range(r0, r1 + 1):
        y = (r - r0) * 40 * z
        dr.text((2, y + 4), str(r), fill=(255, 255, 0), font=lab)
        for c, ch in enumerate(mk_tbl.ROWS[r] if r < len(mk_tbl.ROWS) else ""):
            x = 30 + c * 18 * z
            g = cell(img, r, c).resize((18 * z, 16 * z), Image.NEAREST)
            out.paste(Image.merge("RGB", (g, g, g)), (x, y))
            dr.text((x, y + 17 * z), ch, fill=(120, 255, 120), font=big)
            dr.text((x, y + 33 * z), str(c), fill=(150, 150, 150), font=lab)
    out.save(a.sheet)
    print(a.sheet)


if __name__ == "__main__":
    main()
