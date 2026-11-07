"""Read-only map of a game PRX: applies its .rel relocations so pointers in .data/.rodata and lui/addiu pairs can be
followed, then answers "who references this string or function".

    python -X utf8 tools/debug/prxmap.py PRX names            every named exec/draw/process string, its refs
    python -X utf8 tools/debug/prxmap.py PRX xref 0xADDR      code and data references to a module-relative address
    python -X utf8 tools/debug/prxmap.py PRX dis 0xADDR [N]   disassemble N instructions (relocations applied)

Addresses are module-relative (vaddr in the ELF); at run time add the load base (tools/debug/warp.py prints it)."""
import re, struct, sys

import capstone

R_MIPS_32, R_MIPS_26, R_MIPS_HI16, R_MIPS_LO16 = 2, 4, 5, 6


class Prx:
    def __init__(self, path):
        d = open(path, 'rb').read()
        phoff, shoff = struct.unpack_from('<II', d, 28)
        shn, ssi = struct.unpack_from('<HH', d, 48)
        self.segs = [struct.unpack_from('<8I', d, phoff + 32 * i) for i in range(2)]   # type off vaddr paddr filesz memsz
        self.img = bytearray(max(s[2] + s[5] for s in self.segs))
        for s in self.segs:
            self.img[s[2]:s[2] + s[4]] = d[s[1]:s[1] + s[4]]
        sh = [struct.unpack_from('<10I', d, shoff + 40 * i) for i in range(shn)]
        stro = sh[ssi][4]
        self.sec = {d[stro + s[0]:d.index(b'\0', stro + s[0])].decode(): s for s in sh}
        self.text = self.sec['.text']
        self.relocs = []
        for s in sh:
            if s[1] == 0x700000a0:
                for o in range(s[4], s[4] + s[5], 8):
                    off, info = struct.unpack_from('<II', d, o)
                    self.relocs.append((off + self.segs[info >> 8 & 255][2], info & 255))

    def word(self, a): return struct.unpack_from('<I', self.img, a)[0]

    def code_refs(self):
        """(instruction address, target) for every lui+addiu/ori/load/store pair and every jal."""
        out = []
        base = self.text[3]
        for a in range(base, base + self.text[5], 4):
            w = self.word(a)
            if w >> 26 == 3: out.append((a, (w & 0x3ffffff) << 2))
            if w >> 26 != 15: continue
            rt = w >> 16 & 31; hi = (w & 0xffff) << 16
            for b in range(a + 4, min(a + 64, base + self.text[5]), 4):
                x = self.word(b); op = x >> 26; rs = x >> 21 & 31
                if rs == rt and op in (8, 9, 13, 32, 33, 35, 36, 37, 40, 41, 43):
                    lo = x & 0xffff
                    if op != 13: lo = lo - 0x10000 if lo & 0x8000 else lo
                    out.append((b, hi + lo))
                    if op in (8, 9, 13) and (x >> 16 & 31) == rt: break
        return out

    def data_refs(self):
        return [(a, self.word(a)) for a, t in self.relocs if t == R_MIPS_32]

    def dis(self, addr, n):
        md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 | capstone.CS_MODE_LITTLE_ENDIAN)
        for i in md.disasm(bytes(self.img[addr:addr + 4 * n]), addr):
            print(f'{i.address:08x}  {i.mnemonic:8} {i.op_str}')


def main():
    p = Prx(sys.argv[1]); cmd = sys.argv[2]
    if cmd == 'dis':
        p.dis(int(sys.argv[3], 16), int(sys.argv[4]) if len(sys.argv) > 4 else 40)
    elif cmd == 'xref':
        t = int(sys.argv[3], 16)
        for a, v in p.code_refs():
            if v == t: print(f'code {a:08x}')
        for a, v in p.data_refs():
            if v == t: print(f'data {a:08x}')
    elif cmd == 'names':
        code = {}
        for a, v in p.code_refs() + p.data_refs(): code.setdefault(v, []).append(a)
        for m in re.finditer(rb'[A-Z][A-Za-z]*(Exec|Draw|Process|Init)\0', bytes(p.img)):
            print(f'{m.start():08x} {m.group()[:-1].decode():24} refs ' + ' '.join(f'{r:x}' for r in code.get(m.start(), [])))


if __name__ == '__main__':
    main()
