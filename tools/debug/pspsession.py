"""PPSSPP session over psp.py for the warp tools: boot, button presses by frame count, memory reads and writes.

Addresses given to rd/wr are absolute; `mod(off)` turns a module-relative ELF address into one, and G is the game's
singleton (the pointer at module 0x351098 in Kai; see tools/debug/README.md)."""
import atexit, base64, json, os, shutil, struct, sys, types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from skill import SKILL  # noqa: E402

sys.path.insert(0, os.path.join(SKILL, 'scripts'))
import psp  # noqa: E402

# PPSSPP's log events can carry raw Shift-JIS from the game; psp.WS.recv would die on them (docs/skill-gotchas.md)
psp.json = types.SimpleNamespace(loads=lambda d: json.loads(d.decode('utf-8', 'replace')), dumps=json.dumps)

ISO ='rom/Goku Makai-Mura Kai (Japan).iso'


class Session:
    def __init__(self, out, iso=ISO, state=None, sav=None, keep_ms=False):
        self.ms = os.path.abspath(os.path.join(out, 'memstick'))
        if not keep_ms: shutil.rmtree(self.ms, ignore_errors=True)
        if sav: psp.seed_saves(self.ms, sav)
        self.r = psp.Run(psp.find_emu(None), iso, out, state, memstick=self.ms)
        self.r.ws.s.settimeout(300)
        self.ws = self.r.ws; self.out = out; self.f = 0
        atexit.register(self.close)   # a crashed script must not leave its emulator running

    def run(self, n=1):
        self.f += n; self.r.run_to(self.f)

    def press(self, keys, hold=6, gap=20):
        self.r.press(set(keys.split('+'))); self.run(hold)
        self.r.press(set()); self.run(gap)

    def hold(self, keys): self.r.press(set(keys.split('+')) if keys else set())

    def shot(self, name): return self.r.shot(name if name.endswith('.png') else name + '.png')

    def rd(self, a, n): return self.ws.mem(a, n)
    def u32(self, a): return struct.unpack('<I', self.rd(a, 4))[0]
    def wr(self, a, data): self.ws.call('memory.write', address=a, base64=base64.b64encode(data).decode())
    def w32(self, a, v): self.wr(a, struct.pack('<I', v & 0xffffffff))

    def modules(self): return self.ws.call('hle.module.list')['modules']

    def base(self, name):
        for m in self.modules():
            if name in m['name']: return m['address']
        raise KeyError(name)

    def close(self): self.r.close()
