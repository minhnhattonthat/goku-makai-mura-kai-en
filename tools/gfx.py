"""gfx.py: the texture edits the build makes (phase 8; survey docs/re/graphics.md, USA disc docs/re/usa.md).

Usage: gfx.py   prints, per game, every archive member the build changes and which textures in it

Rules (D10: the USA disc's English art wins wherever the tree matches):
- Per texture (GIM) inside an ANA, both games: a GIM equal to the original game's GIM takes the USA GIM paired with it
  (same name, same occurrence of that name), spliced in place (sizes must match, so the ANA's offsets and trailing data
  stay). A Kai-only or Kai-changed GIM is left alone. Never the USA button icons (KEEP_JP); a60 only ONLY's names.
  (Whole USA files are wrong here: their button icons swap circle and cross.)
  ANA bytes outside the GIMs (sprite geometry; a03's tab dividers) take the USA's changes like a .csl, when the
  three ANAs have the same length.
- REDRAW: our own lettering for what the USA art doesn't cover, written over the result.
- .csl layouts (same length in all three): Kai takes the USA's byte changes wherever its own bytes equal the original's.
  a60.csl differs in length (another title layout): both games keep their own.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ana
import bms
import build
import gim
import kpd

D2 = "pkdata/{}.kpd/2d/{}/{}.{}"
# (kpd, ana) of every texture set the USA disc changed; a03 (sub screen) exists only in the original game
SETS = [("play_res", "a00"), ("play_res", "a02"), ("play_res", "a03"), ("play_res", "a10"), ("loading", "a06"),
        ("st_select", "a30"), ("title", "a60"), ("ending", "a70")]
ARCH = {"re": build.USR + "REGOKUMAKAI/datapack.kpd", "go": build.USR + "GOKUMAKAI/datapack.kpd",
        "la": build.USR + "LAUNCHER/LAUNCHER.KPD"}
A06 = D2.format("loading", "a06", "a06", "ana")
MAZO = "pkdata/s0a00_stg.kpd/stage/s0a/s0a00/gim/s0a0001mazo.gim"
# a60: the USA title packs its menu labels another way (its tit_w_0 under our layout drew OPTIONS where NEW GAME goes,
# work/qa/p8gfx/cmp_title.png), and ours are English already: take only the intro story, and the logo for the original
# game. Kai keeps its Japanese logo (D5: no official English Kai logo).
# button0: the USA swapped the circle and cross icons (its OK is cross); this code confirms with circle, so the JP icons
# stay, and the USA word art (DECIDE, BACK) lands beside them in the original order (work/qa/p8gfx/cmp_btn.png)
KEEP_JP = {"button0"}
ONLY = {("go", D2.format("title", "a60", "a60", "ana")): {"op_w_00", "logo_go"},
        ("re", D2.format("title", "a60", "a60", "ana")): {"op_w_00"}}


def tree(iso, path):
    return dict(kpd.walk(build.read_files(iso, [path])[path]))


def gims(d):
    """[(name, occurrence of that name, offset, size)]"""
    seen, out = {}, []
    for o, s, n in ana.parse(d):
        seen[n] = seen.get(n, -1) + 1
        out.append((n, seen[n], o, s))
    return out


def splice(x, orig, us, only=None):
    """x (an ANA) with each GIM that equals one of orig's replaced by the USA GIM paired with it (only: names allowed);
    [names replaced]."""
    pair = {(n, k): us[o:o + s] for n, k, o, s in gims(us) if (only is None or n in only) and n not in KEEP_JP}
    by_bytes = {orig[o:o + s]: (n, k) for n, k, o, s in gims(orig)}
    out, done = bytearray(x), []
    for n, k, o, s in gims(x):
        new = pair.get(by_bytes.get(x[o:o + s]))
        if new is None or new == x[o:o + s]:
            continue
        assert len(new) == s, f"{n}#{k}: USA GIM is {len(new)} bytes, ours {s}"
        out[o:o + s] = new
        done.append(n)
    if only is None and len(x) == len(orig) == len(us):
        # bytes outside the GIMs are sprite geometry (a03: the USA moved the tab dividers): the USA's changes, as in .csl
        m, pos = merge3(x, orig, us), 0
        for o, s in sorted((o, s) for _, _, o, s in gims(x)) + [(len(x), 0)]:
            if out[pos:o] != m[pos:o]:
                out[pos:o] = m[pos:o]
                done.append(f"geometry@{pos:#x}")
            pos = max(pos, o + s)
    return bytes(out), done


def merge3(x, orig, us):
    """Bytes of x, with the USA's change wherever x still equals the original."""
    assert len(x) == len(orig) == len(us)
    return bytes(c if a == b else a for a, b, c in zip(x, orig, us))


def rgba(d):
    """(w, h, [bytearray RGBA row]) of a GIM's first image."""
    w, h, rows = gim.to_rgba(d, gim.parse(d)[0])
    return w, h, [bytearray(r) for r in rows]


def ink_cols(rows, y0, y1, x0=0, x1=None, alpha=1):
    """[(start, end)] column runs with a pixel of at least this alpha in rows y0..y1-1, x0..x1-1."""
    x1 = x1 or len(rows[0]) // 4
    on = [any(rows[y][4 * x + 3] >= alpha for y in range(y0, y1)) for x in range(x0, x1)]
    out, s = [], None
    for i, v in enumerate(on + [False]):
        if v and s is None:
            s = i
        elif not v and s is not None:
            out.append((x0 + s, x0 + i))
            s = None
    return out


def ink_rows(rows):
    """[(start, end)] row bands with any opaque pixel."""
    on = [any(r[3::4]) for r in rows]
    out, s = [], None
    for i, v in enumerate(on + [False]):
        if v and s is None:
            s = i
        elif not v and s is not None:
            out.append((s, i))
            s = None
    return out


class Font:
    """Letters cut from the USA's own lettering: add(rows, band, text) labels each ink column run of a band with the
    next non-space character of text (asserts one run per letter), word(text) composes a line of them."""
    def __init__(self, gap, space):
        self.g, self.gap, self.space = {}, gap, space

    def add(self, rows, y0, y1, text, x0=0, x1=None):
        # letters split on their solid ink (antialiased edges touch), each cut at the midpoints between neighbours
        runs, chars = ink_cols(rows, y0, y1, x0, x1, alpha=128), text.replace(" ", "")
        col = lambda x: sum(rows[y][4 * x + 3] for y in range(y0, y1))
        while 0 < len(runs) < len(chars):   # two letters still touch (TT, DE): split the widest run at its faintest column
            i = max(range(len(runs)), key=lambda k: runs[k][1] - runs[k][0])
            a, b = runs[i]
            if b - a < 8:
                break
            x = min(range(a + 3, b - 3), key=col)
            runs[i:i + 1] = [(a, x), (x + 1, b)]
        if len(runs) != len(chars):
            return   # letters that touch even in solid ink (DECIDE): take them from another word
        edge = [runs[0][0] - 1] + [(b + c) // 2 for (_, b), (c, _) in zip(runs, runs[1:])] + [runs[-1][1] + 1]
        for (a, b), (lo, hi), c in zip(runs, zip(edge, edge[1:]), chars):
            lo, hi = max(lo, a - 1), min(hi, b + 1)   # the solid ink plus its antialiased rim
            self.g.setdefault(c, ([r[4 * lo:4 * hi] for r in rows[y0:y1]], a - lo, b - a))

    def check(self, text):
        missing = set(text) - set(self.g) - {" "}
        assert not missing, f"no clean cut of {sorted(missing)}"

    def width(self, text):
        """Solid-ink width of text drawn with draw()."""
        return sum(self.space if c == " " else self.g[c][2] + self.gap for c in text) - self.gap

    def draw(self, rows, x, y, text):
        """text with its first letter's solid ink at column x, the glyph tops at row y."""
        self.check(text)
        for c in text:
            if c == " ":
                x += self.space
                continue
            px, lead, solid = self.g[c]
            for i, line in enumerate(px):
                for j in range(len(line) // 4):
                    if line[4 * j + 3]:
                        at = 4 * (x - lead + j)
                        rows[y + i][at:at + 4] = line[4 * j:4 * j + 4]
            x += solid + self.gap


def clear(rows, x0, y0, x1, y1):
    for y in range(y0, y1):
        rows[y][4 * x0:4 * x1] = bytes(4 * (x1 - x0))


def a10_font(us):
    """The option screen's letters: USA a10 18 (button functions) and 20 (legend)."""
    t18, t20 = (rgba(gim_of(us, "pkdata/play_res.kpd/2d/a10/a10.ana", n))[2] for n in ("18_op_wor0", "20_op_wor0"))
    f = Font(gap=1, space=10)   # USA spacing: 1 px between solid strokes, 11 between words (WARP STAFF)
    b20 = ink_rows(t20)
    for (y0, y1), (left, right) in zip(b20, [("MOVE", "CURSOR"), ("MENU", "DECIDE"), ("SUBSCREEN", "CANCEL")]):
        f.add(t20, y0, y1, left, 0, 128)
        f.add(t20, y0, y1, right, 128)
    words = list(zip(ink_rows(t18), ["EQUIP MAGIC", "EQUIP SHIELD", "WARP STAFF", "MAGIC POWER", "JUMP", "ATTACK"]))
    for (y0, y1), text in words[::-1]:   # ATTACK first: its TT splits cleanly, STAFF's TA doesn't
        f.add(t18, y0, y1, text)
    return f, t18, t20


def gim_of(d, member, name):
    a = d[member]
    for i, (o, s, n) in enumerate(ana.parse(a)):
        if f"{i:02d}_{n}" == name:
            return a[o:o + s]
    raise KeyError(name)


def re_a10_18(us, _):
    """Kai's button functions: 魔力 魔力 使用しない 魔力 ジャンプ 攻撃 = MAGIC POWER x2, NOT USED, MAGIC POWER, JUMP, ATTACK
    (USA wording for 魔力 on this screen: MAGIC POWER)."""
    f, rows, _ = a10_font(us)
    b = ink_rows(rows)
    pitch = b[1][0] - b[0][0]
    top = lambda k: b[0][0] + k * pitch
    src = [bytearray(r) for r in rows[top(3):top(4)]]
    x0 = ink_cols(rows, *b[2])[0][0]
    for k in (0, 1, 2):
        clear(rows, 0, top(k), len(rows[0]) // 4, top(k + 1))
    for k in (0, 1):
        rows[top(k):top(k + 1)] = [bytearray(r) for r in src]
    f.draw(rows, x0, b[2][0], "NOT USED")
    return rows


def re_a10_20(us, _):
    """Kai's legend: the USA one with SUBSCREEN -> PAUSE (ポーズ), centred where SUBSCREEN was."""
    f, _, rows = a10_font(us)
    y0, y1 = ink_rows(rows)[2]
    runs = ink_cols(rows, y0, y1, 0, 128)
    mid = (runs[0][0] + runs[-1][1]) // 2
    clear(rows, 0, y0, 128, y1)
    f.draw(rows, mid - f.width("PAUSE") // 2, y0, "PAUSE")
    return rows


def game_font():
    """(bft, sheet rows, table) of the font both games ship (build.font_files: the USA font, variable width)."""
    f = build.font_files()
    return f["font/jfont_00.bft"], rgba(f["font/jfont_00.gim"])[2], bms.load_tbl()


def glyphs(font, text):
    """[(sheet x, y, w, h)] per character; one-byte codes only (ASCII)."""
    bft, _, t = font
    b = t.encode(text.replace("\xa0", " "))   # NBSP: a space wrap() doesn't break at
    assert all(c < 0x80 for c in b), text
    return [struct.unpack_from("<5H", bft, 0x2c + c * 10)[1:] for c in b]


def text_width(font, text):
    return sum(g[2] for g in glyphs(font, text))


def write(rows, x, y, text, font, bg):
    """text in the game font, top-left at (x, y), blended over the opaque colour bg."""
    sheet = font[1]
    for sx, sy, w, h in glyphs(font, text):
        for j in range(h):
            for i in range(w):
                p = sheet[sy + j][4 * (sx + i):4 * (sx + i) + 4]
                if p[3]:
                    rows[y + j][4 * (x + i):4 * (x + i) + 4] = bytes(
                        [(c * p[3] + b * (255 - p[3])) // 255 for c, b in zip(p[:3], bg[:3])] + [255])
        x += w


def wrap(font, text, width):
    lines = [""]
    for w in text.split(" "):
        t = (lines[-1] + " " + w).strip()
        if text_width(font, t) <= width or not lines[-1]:
            lines[-1] = t
        else:
            lines.append(w)
    return lines


# a60 op_w_01: the original game's notice when the card holds a ULJM-05147 (standalone 極魔界村 disc) save; the go
# memstick:11 text is the same notice (D12 titles). The logo stays: it is that disc's save icon, as the picker shows it.
GO, KAI = "\"Ultimate\xa0Ghosts\xa0'n\xa0Goblins\"", "\"Ultimate\xa0Ghosts\xa0'n\xa0Goblins\xa0Kai\""
OPW01_HEAD = f"Game data from the {GO} disc has been detected."
OPW01_BODY = [f"To load this game data on the {KAI} disc, choose \"LOAD\xa0GAME\" on the title menu, then select the "
              "icon above.",
              f"Game data created on the {KAI} disc cannot be loaded on the {GO} disc."]


def op_w_01(us, rows):
    font, bg = game_font(), bytes(rows[0][:4])
    logo = (40, 24, 200, 116)   # the logo's box; everything else is the JP text on a flat background
    for y, r in enumerate(rows):
        for x in range(len(r) // 4):
            if not (logo[0] <= x < logo[2] and logo[1] <= y < logo[3]):
                r[4 * x:4 * x + 4] = bg
    head = wrap(font, OPW01_HEAD, 470 - 208)
    y = (logo[1] + logo[3]) // 2 - 17 * len(head) // 2
    for line in head:
        write(rows, 208, y, line, font, bg)
        y += 17
    y = 128
    for para in OPW01_BODY:
        for line in wrap(font, para, 440 - 40):
            write(rows, 40, y, line, font, bg)
            y += 17
        y += 10
    assert y - 10 <= 262, y
    return rows


def op_w_00(us, rows):
    """The USA intro story with its two paragraph gaps 14 px shorter: the JP scroll stops when the JP text (ink to row
    453) has left the top, and the USA's ends at row 476, so its last line stayed on screen over the movie."""
    out, shift, prev = [bytearray(len(rows[0])) for _ in rows], 0, None
    for y0, y1 in ink_rows(rows):
        shift += 14 if prev is not None and y0 - prev > 40 else 0   # line pitch 24, paragraph gap 48
        out[y0 - shift:y1 - shift], prev = rows[y0:y1], y0
    assert ink_rows(out)[-1][1] <= 453, ink_rows(out)[-1]
    return out


# redraws: (game, member, GIM "NN_name") -> fn(usa tree, base RGBA rows) giving the RGBA rows; the USA GIM of the same
# size and name is the base (its palette holds the lettering's colours), else our own GIM
A60 = "pkdata/title.kpd/2d/a60/a60.ana"
REDRAW = {("re", "pkdata/play_res.kpd/2d/a10/a10.ana", "18_op_wor0"): re_a10_18,
          ("re", "pkdata/play_res.kpd/2d/a10/a10.ana", "20_op_wor0"): re_a10_20,
          ("go", A60, "16_op_w_00"): op_w_00,
          ("re", A60, "20_op_w_00"): op_w_00,
          ("go", A60, "23_op_w_01"): op_w_01,
          ("re", A60, "27_op_w_01"): op_w_01}   # same image; Kai never shows it (its PRX has no ULJM05147)


def redraw(game, member, data, us):
    """data (an ANA) with this game's REDRAW entries written; [names]."""
    out, done = bytearray(data), []
    for i, (o, s, n) in enumerate(ana.parse(data)):
        fn = REDRAW.get((game, member, f"{i:02d}_{n}"))
        if fn is None:
            continue
        try:
            base = gim_of(us, member, f"{i:02d}_{n}")
        except KeyError:
            base = data[o:o + s]
        base = base if len(base) == s else data[o:o + s]
        out[o:o + s] = gim.encode(base, gim.parse(base)[0], fn(us, rgba(base)[2]))
        done.append(f"{i:02d}_{n}")
    return bytes(out), done


def mazo(d):
    """Stage 0a's stone texture with the dev mark 仮 removed (the USA left it): its strokes are the only green-tinted
    pixels in that box; they are filled from their neighbours, then mapped back to the 16-colour palette."""
    img = gim.parse(d)[0]
    w, h, rows = rgba(d)
    x0, y0, x1, y1 = MAZO_BOX
    hole = {(x, y) for y in range(y0, y1) for x in range(x0, x1) if rows[y][4 * x + 1] > rows[y][4 * x] + 4}
    hole |= {(x + dx, y + dy) for x, y in hole for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}   # the dark rim
    while hole:
        fill = {}
        for x, y in hole:
            near = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if 0 <= x + dx < w and 0 <= y + dy < h and (x + dx, y + dy) not in hole]
            if near:
                fill[x, y] = bytes([sum(rows[b][4 * a + k] for a, b in near) // len(near) for k in range(3)] + [255])
        assert fill
        for (x, y), p in fill.items():
            rows[y][4 * x:4 * x + 4] = p
        hole -= set(fill)
    return gim.encode(d, img, rows, repalette=False)


MAZO_BOX = (35, 49, 63, 72)   # 仮 in s0a0001mazo (64x128), x0, y0, x1, y1


def edits(trees=None):
    """{archive key ("re", "go", "la"): {member: (bytes, note)}} for the members whose bytes change."""
    t = trees or {g: tree(build.ROM, p) for g, p in ARCH.items()}
    t.setdefault("us", tree(build.US_ROM, build.USR + "datapack.kpd"))
    go, us = t["go"], t["us"]
    out = {"re": {}, "go": {}, "la": {}}
    # the launcher's loading word (次へ) is the games' a06 door_w0: the USA one, as in the games
    m = "2d/a50/a50.ana"
    new, done = splice(t["la"][m], go[A06], us[A06])
    out["la"][m] = (new, "USA GIMs " + " ".join(done))
    for game in ("re", "go"):
        out[game][MAZO] = (mazo(t[game][MAZO]), "仮 removed")
    for k, a in SETS:
        for x in ("ana", "csl"):
            m = D2.format(k, a, a, x)
            if m not in us:
                continue
            for game in out:
                own = t[game].get(m)
                if own is None:
                    continue
                if x == "ana":
                    new, done = splice(own, go[m], us[m], ONLY.get((game, m)))
                    note = "USA GIMs " + " ".join(done)
                elif len(own) == len(go[m]) == len(us[m]):
                    new, note = merge3(own, go[m], us[m]), "USA layout changes"
                else:
                    continue   # a60.csl: the USA title layout is another structure; each game keeps its own
                if x == "ana":
                    new, done = redraw(game, m, new, us)
                    note += "; redrawn " + " ".join(done) if done else ""
                if new != own:
                    out[game][m] = (new, note)
    return out


def files():
    """{datapack iso path: {member: bytes}} for build.edits()."""
    return {ARCH[g]: {m: b for m, (b, _) in e.items()} for g, e in edits().items()}


if __name__ == "__main__":
    out = build.ROOT / "work" / "gfx" / "out"
    out.mkdir(parents=True, exist_ok=True)
    for game, e in edits().items():
        for m, (b, note) in sorted(e.items()):
            print(game, m, note)
            if m.endswith(".gim"):
                w, h, rows = gim.to_rgba(b, gim.parse(b)[0])
                gim.save_png(str(out / f"{game}_{Path(m).stem}.png"), w, h, rows)
            if m.endswith(".ana"):   # previews of the redrawn GIMs: work/gfx/out/<game>_<NN_name>.png
                for i, (o, s, n) in enumerate(ana.parse(b)):
                    if (game, m, f"{i:02d}_{n}") in REDRAW:
                        w, h, rows = gim.to_rgba(b[o:o + s], gim.parse(b[o:o + s])[0])
                        gim.save_png(str(out / f"{game}_{i:02d}_{n}.png"), w, h, rows)
