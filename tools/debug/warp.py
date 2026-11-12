"""Warp to any scene from a cold boot, for both games: drives PPSSPPHeadless over psp.py and pokes RAM only; no file on
the disc changes, so it runs against the original ISO or any build.

    python -X utf8 tools/debug/warp.py --list
    python -X utf8 tools/debug/warp.py re:stage_0201 --out work/qa/warp [--iso build/goku_en.iso]
    python -X utf8 tools/debug/warp.py --all [--game re] [--only SUBSTR] --out work/qa/warp   regenerate every state and shot
Each scene writes OUT/<game>_<scene>.png and work/states/<game>_<scene>.ppst, and fails (exit 1) unless the scene's
RAM check holds: the process it names must be in the game's live process chain.

How it works (tools/debug/README.md): the game is a stack of static Process objects. `redirect()` writes a small stub
into RAM and points one `jal factory` at it, so the title's NEW GAME (or the stage's START) opens the wanted process."""
import argparse, os, struct, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pspsession import Session, ISO  # noqa: E402
import scenes as sc  # noqa: E402

STUB = 0x08800100    # below the module, unused by the game
BASE = 0x08804000    # both games load here (asserted at boot)
MODE_OK = {0, 1, 2, 3}


HOOK = 0x08800800    # text-log stub (below the scratch string at 0x08801000)
RING = 0x08802000    # u32 count, then 256 entries of 16 bytes at +0x10: bms count, last offset word, index, bms
LW_A0, LW_A2 = 0x8c840000, 0x8c860000    # the getter's first two words: lw a0,0(a0); lw a2,0(a0)


def ori(reg, imm): return 0x34000000 | reg << 16 | imm
def jal(a): return 0x0c000000 | (a & 0x0fffffff) >> 2
def j(a): return 0x08000000 | (a & 0x0fffffff) >> 2


def hook_code(getter):
    """Stub the getter jumps to: its own two loads, then a ring-buffer entry (t0-t3 only: caller-saved), then back."""
    return [LW_A0, LW_A2,
            0x3c080880, 0x8d092000,    # lui t0,0x0880; lw t1,0x2000(t0)       t1 = entries written
            0x312a00ff, 0x000a5100,    # andi t2,t1,0xff; sll t2,t2,4
            0x01485021, 0x8ccb0000,    # addu t2,t2,t0; lw t3,0(a2)             t3 = string count
            0xad4b2010, 0x000b5880,    # sw t3,0x2010(t2); sll t3,t3,2
            0x01665821, 0x8d6b0000,    # addu t3,t3,a2; lw t3,0(t3)             t3 = last offset word
            0xad4b2014, 0xad452018,    # sw t3,0x2014(t2); sw a1,0x2018(t2)
            0xad46201c, 0x25290001,    # sw a2,0x201c(t2); addiu t1,t1,1
            0xad092000, j(getter + 8), 0]   # sw t1,0x2000(t0); j getter+8; nop


class Game:
    def __init__(self, g, out, iso=ISO, state=None, sav=None, keep_ms=False):
        self.g = g; self.a = sc.ADDR[g]; self.s = Session(out, iso, state, sav, keep_ms)
        self.G = None; self.out = out; self.stub = STUB
        self.textlog = None; self.ring_n = 0

    def mod(self, off): return BASE + off

    def hook_text(self):
        """Every .bms getter call (obj -> p -> bms; a1 = index) goes to OUT/textlog.txt as `TEXT <count> <last offset
        word> <index> <first 64 bytes of the file>` (hex), for tools/cover.py: the getter jumps to a stub that fills a
        RAM ring, read after each run()."""
        gt = self.mod(self.a['getter'])
        if self.s.u32(gt) != LW_A0: return    # hooked already (attach again) or not the getter
        assert self.s.u32(gt + 4) == LW_A2, 'getter changed, redo the hook'
        self.textlog = open(os.path.join(self.out, 'textlog.txt'), 'w', newline='\n')
        self.s.wr(RING, b'\0' * 4); self.ring_n = 0
        self.s.wr(HOOK, struct.pack('<19I', *hook_code(gt)))
        self.s.wr(gt, struct.pack('<II', j(HOOK), 0))
        self.s.after_run = self.read_text

    def read_text(self):
        n = self.s.u32(RING)
        if n < self.ring_n: self.ring_n = 0    # a state load rolled RAM back
        if n - self.ring_n > 256: print(f'textlog: {n - self.ring_n - 256} getter calls lost'); self.ring_n = n - 256
        if n == self.ring_n: return
        ring = self.s.rd(RING + 0x10, 0x1000); head = {}
        for k in range(self.ring_n, n):
            c, last, i, bms = struct.unpack_from('<4I', ring, (k & 0xff) * 16)
            if bms not in head:   # names the file: (count, last) alone doesn't
                try: head[bms] = self.s.rd(bms, 64).hex()
                except Exception: head[bms] = '-'
            self.textlog.write(f'TEXT {c:x} {last:x} {i:x} {head[bms]}\n')
        self.ring_n = n

    def attach(self):
        """Call once the game module runs: reads the singleton and checks the build matches the address table."""
        mods = [m for m in self.s.modules() if m['name'] == 'Makaimura' and m['isActive']]
        assert mods and mods[0]['address'] == BASE, f'game module not at {BASE:x}: {mods}'
        self.G = self.s.u32(self.mod(self.a['G']))
        assert 0x08800000 < self.G < 0x0a000000, f'bad singleton {self.G:x}'
        for site in ('stage_read', 'area_read'):
            w = self.s.u32(self.mod(self.a[site]))
            assert w == self.a[site + '_orig'], f'{site}: {w:x}: PRX layout changed, redo the address table'
        self.hook_text()

    @property
    def sys(self): return self.G + self.a['sys']

    def chain(self):
        """Names of the live processes, head first (walks the task list; unknown objects print as hex)."""
        if self.G is None: return []    # still in the launcher
        names ={BASE + o: n for n, (_, o) in self.a['proc'].items()}
        out = []; p = self.s.u32(self.sys + 0x14)
        for _ in range(16):
            if not p: break
            out.append(names.get(p, hex(p)))
            if p == self.s.u32(self.sys + 0x18): break
            p = self.s.u32(p)
        return out

    def stage(self):
        if self.G is None: return None
        return self.s.u32(self.G + self.a['stage_off']), self.s.u32(self.G + self.a['stage_off'] + 4)

    def wait(self, pred, maxf=3000, step=10, what=''):
        for _ in range(0, maxf, step):
            if pred(): return True
            self.s.run(step)
        raise TimeoutError(f'{what or pred} after {maxf} frames; chain {self.chain()}')

    def wait_proc(self, name, maxf=3000): self.wait(lambda: name in self.chain(), maxf, what=name)

    def redirect(self, site, factory, a1=None, fields=()):
        """Make the `jal` at module SITE call FACTORY (a process name) instead, with a1 set and FIELDS (offset, value)
        written into the returned object. RAM only."""
        fac = self.mod(self.a['proc'][factory][0])
        c = [0x27bdfff0, 0xafbf0000]                        # addiu sp,-16; sw ra,0(sp)
        if a1 is not None: c += [ori(5, a1)]
        c += [jal(fac), 0]
        for off, val in fields: c += [ori(8, val), 0xac480000 | off]   # ori t0; sw t0,off(v0)
        c += [0x8fbf0000, 0x03e00008, 0x27bd0010]           # lw ra,0(sp); jr ra; addiu sp,16
        self.s.wr(self.stub, struct.pack(f'<{len(c)}I', *c))
        self.s.w32(self.mod(site), jal(self.stub))
        self.stub += 0x40

    def force_stage(self, stage, area):
        """Replace the two instructions that read the stage and area ids, so the next load enters this one."""
        self.s.w32(self.mod(self.a['stage_read']), ori(5, stage))
        self.s.w32(self.mod(self.a['area_read']), ori(5, area))

    def unforce_stage(self):
        for k in ('stage_read', 'area_read'): self.s.w32(self.mod(self.a[k]), self.a[k + '_orig'])

    def shot(self, name): return self.s.shot(f'{self.g}_{name}')

    def close(self):
        if self.textlog:
            try: self.read_text()
            except Exception: pass    # emulator already gone
            self.textlog.close()
        self.s.close()


def run_scene(game, name, out, iso=ISO, state_out=True, tail=0, every=120, keys=''):
    r = sc.SCENES[game][name]
    os.makedirs(out, exist_ok=True)
    sav = r.get('sav')
    g = Game(game, os.path.join(out, 'run', f'{game}_{name}'), iso, sav=sav() if callable(sav) else sav)
    t = time.time()
    try:
        r['go'](g)
        ch = g.chain()
        need = r.get('proc')
        ok = need is None or need in ch
        if ok and r.get('check'): ok = r['check'](g)
        png = g.s.shot(name)
        target = os.path.join(out, f'{game}_{name}.png')
        os.replace(png, target)
        if state_out:   # a build's states go in their own folder, so the original's stay
            sd = 'work/states' if os.path.samefile(iso, ISO) else f'work/states/{os.path.splitext(os.path.basename(iso))[0]}'
            os.makedirs(sd, exist_ok=True)
            g.s.r.save_state(f'{sd}/{game}_{name}.ppst')
        for i, k in enumerate(keys.split()):    # scripted presses ("right*300" holds), one shot each: for exploring
            b, _, n = k.partition('*')
            g.s.press(b, hold=int(n or 6), gap=every); g.s.shot(f'k{i:02d}_{b}'); print(i, k, g.chain())
        for i in range(tail // every):
            g.s.run(every); g.s.shot(f't{g.s.f:06d}')
        print(f'{"ok  " if ok else "FAIL"} {game}:{name:24} {g.stage()} {ch} f{g.s.f} {time.time() - t:.0f}s')
        return ok
    except Exception as e:
        print(f'FAIL {game}:{name:24} {type(e).__name__}: {e} f{g.s.f}')
        try: g.s.shot(name); os.replace(os.path.join(g.out, name + '.png'), os.path.join(out, f'{game}_{name}_FAIL.png'))
        except Exception: pass
        return False
    finally:
        g.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('scene', nargs='?'); ap.add_argument('--out', default='work/qa/warp'); ap.add_argument('--iso', default=ISO)
    ap.add_argument('--list', action='store_true'); ap.add_argument('--all', action='store_true')
    ap.add_argument('--game'); ap.add_argument('--only', default=''); ap.add_argument('--skip', default='\0')
    ap.add_argument('--tail', type=int, default=0, help='keep running N frames, a shot every --every, into OUT/run/<scene>/')
    ap.add_argument('--every', type=int, default=120); ap.add_argument('--keys', default='', help='presses after the scene, a shot each')
    a = ap.parse_args()
    if a.list:
        for g in sc.SCENES:
            for n, r in sc.SCENES[g].items(): print(f'{g}:{n:24} {r.get("doc", "")}')
        return
    todo = [tuple(a.scene.split(':'))] if a.scene else [(g, n) for g in sc.SCENES for n in sc.SCENES[g]
                                                       if (not a.game or g == a.game) and a.only in n and a.skip not in n]
    bad = [f'{g}:{n}' for g, n in todo if not run_scene(g, n, a.out, a.iso, tail=a.tail, every=a.every, keys=a.keys)]
    print(f'{len(todo) - len(bad)}/{len(todo)} ok' + (f'; failed {bad}' if bad else ''))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
