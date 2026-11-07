"""Function starts in a PRX (addiu $sp,-N prologues) and callers of each.

    python -X utf8 tools/debug/prxfunc.py PRX of 0xADDR..        function containing each address, with its callers
    python -X utf8 tools/debug/prxfunc.py PRX fields 0xGLOBAL    offsets read/written through a global pointer: lw r,GLOBAL ; lw/sw x,off(r)"""
import bisect, sys

from prxmap import Prx


def starts(p):
    t = p.text; base = t[3]
    out = []
    for a in range(base, base + t[5], 4):
        w = p.word(a)
        if w >> 16 == 0x27bd and w & 0x8000:  # addiu sp,sp,-N
            out.append(a)
    return out


def main():
    p = Prx(sys.argv[1]); cmd = sys.argv[2]
    st = starts(p)
    if cmd == 'of':
        calls = {}
        for a, v in p.code_refs():
            calls.setdefault(v, []).append(a)
        data = {}
        for a, v in p.data_refs():
            data.setdefault(v, []).append(a)
        for x in sys.argv[3:]:
            a = int(x, 16); f = st[bisect.bisect_right(st, a) - 1]
            print(f'{a:x} in {f:x}: called from ' + ' '.join(f'{c:x}' for c in calls.get(f, [])) + ' data ' + ' '.join(f'{c:x}' for c in data.get(f, [])))
    elif cmd == 'fields':
        g = int(sys.argv[3], 16)
        hi = (g + 0x8000) >> 16; lo = g - (hi << 16); seen = {}
        t = p.text
        for a in range(t[3], t[3] + t[5], 4):
            w = p.word(a)
            if w >> 26 != 35 or (w & 0xffff) != (lo & 0xffff): continue
            # lw rt, lo(base): the lui is within the previous 40 instructions
            rs = w >> 21 & 31
            if not any(p.word(b) >> 16 == 0x3c00 | rs and p.word(b) & 0xffff == hi for b in range(a - 160, a, 4)): continue
            r = w >> 16 & 31
            for b in range(a + 4, a + 64, 4):
                x = p.word(b); op = x >> 26
                if (x >> 21 & 31) == r and op in (32, 33, 35, 36, 37, 40, 41, 43, 49, 57):
                    seen.setdefault((x & 0xffff, 'w' if op in (40, 41, 43, 57) else 'r'), []).append(b)
                if op in (9, 15, 35) and (x >> 16 & 31) == r: break
        for (o, k), v in sorted(seen.items()):
            print(f'+{o:04x} {k} {len(v):3}  ' + ' '.join(f'{c:x}' for c in v[:8]))


if __name__ == '__main__':
    main()
