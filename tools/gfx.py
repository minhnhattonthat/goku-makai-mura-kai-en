"""gfx.py: the texture edits the build makes (phase 8; survey docs/re/graphics.md, USA disc docs/re/usa.md).

Usage: gfx.py   prints, per game, every archive member the build changes and which textures in it

Rules (D10: the USA disc's English art wins wherever the tree matches):
- Per texture (GIM) inside an ANA, both games: a GIM equal to the original game's GIM takes the USA GIM paired with it
  (same name, same occurrence of that name), spliced in place (sizes must match, so the ANA's offsets and trailing data
  stay). A Kai-only or Kai-changed GIM is left alone. Never the USA button icons (KEEP_JP); a60 only ONLY's names.
  (Whole USA files are wrong here: their button icons swap circle and cross.)
- REDRAW: our own lettering for what the USA art doesn't cover, written over the result.
- .csl layouts (same length in all three): Kai takes the USA's byte changes wherever its own bytes equal the original's.
  a60.csl differs in length (another title layout): both games keep their own.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ana
import build
import gim
import kpd

D2 = "pkdata/{}.kpd/2d/{}/{}.{}"
# (kpd, ana) of every texture set the USA disc changed; a03 (sub screen) exists only in the original game
SETS = [("play_res", "a00"), ("play_res", "a02"), ("play_res", "a03"), ("play_res", "a10"), ("loading", "a06"),
        ("st_select", "a30"), ("title", "a60"), ("ending", "a70")]
GAMES = {"re": "REGOKUMAKAI", "go": "GOKUMAKAI"}
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


def re_a10_18(us):
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


def re_a10_20(us):
    """Kai's legend: the USA one with SUBSCREEN -> PAUSE (ポーズ), centred where SUBSCREEN was."""
    f, _, rows = a10_font(us)
    y0, y1 = ink_rows(rows)[2]
    runs = ink_cols(rows, y0, y1, 0, 128)
    mid = (runs[0][0] + runs[-1][1]) // 2
    clear(rows, 0, y0, 128, y1)
    f.draw(rows, mid - f.width("PAUSE") // 2, y0, "PAUSE")
    return rows


# redraws: (game, member, GIM "NN_name") -> fn(usa tree) giving the RGBA rows; the USA GIM of the same size and name
# is the base (its palette holds the lettering's colours), else our own GIM
REDRAW = {("re", "pkdata/play_res.kpd/2d/a10/a10.ana", "18_op_wor0"): re_a10_18,
          ("re", "pkdata/play_res.kpd/2d/a10/a10.ana", "20_op_wor0"): re_a10_20}


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
        out[o:o + s] = gim.encode(base, gim.parse(base)[0], fn(us))
        done.append(f"{i:02d}_{n}")
    return bytes(out), done


def edits(trees=None):
    """{game: {member: (bytes, note)}} for the members whose bytes change."""
    t = trees or {"re": tree(build.ROM, build.USR + "REGOKUMAKAI/datapack.kpd"),
                  "go": tree(build.ROM, build.USR + "GOKUMAKAI/datapack.kpd"),
                  "us": tree(build.US_ROM, build.USR + "datapack.kpd")}
    go, us = t["go"], t["us"]
    out = {"re": {}, "go": {}}
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
    return {build.USR + GAMES[g] + "/datapack.kpd": {m: b for m, (b, _) in e.items()} for g, e in edits().items()}


if __name__ == "__main__":
    out = build.ROOT / "work" / "gfx" / "out"
    out.mkdir(parents=True, exist_ok=True)
    for game, e in edits().items():
        for m, (b, note) in sorted(e.items()):
            print(game, m, note)
            if m.endswith(".ana"):   # previews of the redrawn GIMs: work/gfx/out/<game>_<NN_name>.png
                for i, (o, s, n) in enumerate(ana.parse(b)):
                    if (game, m, f"{i:02d}_{n}") in REDRAW:
                        w, h, rows = gim.to_rgba(b[o:o + s], gim.parse(b[o:o + s])[0])
                        gim.save_png(str(out / f"{game}_{i:02d}_{n}.png"), w, h, rows)
