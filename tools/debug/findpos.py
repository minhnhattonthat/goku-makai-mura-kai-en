"""Find float fields that follow Arthur: snapshot RAM, walk right, snapshot, walk left less far, snapshot; keep addresses
whose float rose then fell.

    python -X utf8 tools/debug/findpos.py GAME STATE.ppst"""
import os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import warp  # noqa: E402

LO, HI = 0x08c00000, 0x09f00000


def snap(g):
    b = bytearray()
    for a in range(LO, HI, 0x100000):
        b += g.s.rd(a, 0x100000)
    return b


def main():
    g = warp.Game(sys.argv[1], 'work/qa/findpos', state=sys.argv[2])
    g.attach()
    s = g.s
    s.run(30); a = snap(g)
    s.press('right', hold=40, gap=30); b = snap(g)
    s.press('left', hold=20, gap=30); c = snap(g)
    n = len(a) // 4
    fa, fb, fc = (struct.unpack(f'<{n}f', x[:n * 4]) for x in (a, b, c))
    hits = []
    for i in range(n):
        x, y, z = fa[i], fb[i], fc[i]
        if 1 < abs(x) < 1e5 and 1 < abs(y) < 1e5 and 1 < abs(z) < 1e5 and 5 < y - x < 2000 and 0.2 * (y - x) < y - z < 0.8 * (y - x):
            hits.append((LO + i * 4, x, y, z))
    print(len(hits))
    for h in hits[:80]:
        print(hex(h[0]), h[1:])


if __name__ == '__main__':
    main()
