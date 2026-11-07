"""List every process transition in a PRX: the spin-then-store `bnez self; sw 2,0xc(sys); sw proc,0x10(sys)` sequence,
with the factory jal that made `proc`, and each process's factory, class name and static object.

    python -X utf8 tools/debug/prxtrans.py PRX"""
import bisect, re, sys

from prxmap import Prx
from prxfunc import starts


def main():
    p = Prx(sys.argv[1]); t = p.text; st = starts(p)
    seg1 = p.segs[1][2]
    img = bytes(p.img)
    names = {m.start(): m.group()[:-1].decode() for m in re.finditer(rb'[A-Z][A-Za-z]*Process\0', img)}
    data = {}
    for a, v in p.data_refs(): data.setdefault(v, a)
    # ctor's vtable holds the Process function; a factory is the function just before a function that ... so go by name
    fn_name = {}
    for a, v in p.code_refs():
        if v in names: fn_name[st[bisect.bisect_right(st, a) - 1]] = names[v]
    fac = {}
    for a in range(t[3], t[3] + t[5] - 16, 4):
        w = p.word(a)
        if w >> 26 == 5 and w & 0xffff == 0xffff and p.word(a + 4) == 0:
            if not any(p.word(c) >> 26 == 43 and p.word(c) & 0xffff == 0x10 for c in range(a + 8, a + 24, 4)): continue
            f, site = None, 0
            for c in range(a - 4, a - 60, -4):
                if p.word(c) >> 26 == 3: f = (p.word(c) & 0x3ffffff) << 2; site = c; break
            where = st[bisect.bisect_right(st, a) - 1]
            print(f'{a:06x} in {fn_name.get(where, hex(where)):20} jal@{site:06x} -> {f or 0:06x}')
            if f: fac.setdefault(f, 0)
    print('factories (factory, static object):')
    for f in sorted(fac):
        hi = lo = None
        for a in range(f, f + 48, 4):
            w = p.word(a)
            if w >> 26 == 15: hi = (w & 0xffff) << 16
            if w >> 26 == 9 and w >> 16 & 31 == w >> 21 & 31 and hi is not None:
                lo = w & 0xffff; lo = lo - 0x10000 if lo & 0x8000 else lo
                break
        print(f'{f:06x} obj {seg1 + hi + lo:06x}')


if __name__ == '__main__':
    main()
