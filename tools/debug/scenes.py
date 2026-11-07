"""Scene list for tools/debug/warp.py: per-game address table, then name -> recipe.

proc = (factory, static object), module-relative, from tools/debug/prxtrans.py. A recipe's `go(g)` takes a warp.Game
from a cold boot to the scene; `proc` names the process the scene needs in the live chain."""
import os, shutil, struct

ADDR = {
    're': {
        'G': 0x351098, 'sys': 0x38578, 'stage_off': 0x40, 'book': None,
        'stage_read': 0x4a6a4, 'stage_read_orig': 0x8e650040,    # lw a1,0x40(s3) -> ori a1,zero,stage
        'area_read': 0x50e08, 'area_read_orig': 0x8e650044,      # lw a1,0x44(s3) -> ori a1,zero,area
        'newgame_jal': 0x70060,    # title's jal Play
        'select_jal': 0x322bc,     # area's second jal SystemMenu (SELECT in a stage); mode 1, pushed over the stage
        'proc': {
            'Area': (0x02f854, 0x43e6a0), 'Ending': (0x03328c, 0x43e8a0), 'Equip': (0x0359bc, 0x43efd0),
            'GameOver': (0x03ad6c, 0x43f9b0), 'Ms': (0x03d728, 0x444f30), 'MsSave': (0x03ddb0, 0x4452a0),
            'MsLoad': (0x03e758, 0x445670), 'Option': (0x0424c4, 0x445a60), 'Pause': (0x048eb0, 0x446440),
            'Play': (0x04a208, 0x446544), 'Result': (0x04caf0, 0x446690), 'Stage': (0x050988, 0x446dd4),
            'StageSelect': (0x051ca4, 0x446ec0), 'Submenu': (0x055724, 0x447c10), 'SystemMenu': (0x062d48, 0x449720),
            'TimeOut': (0x06a6e0, 0x44ba40), 'Title': (0x06bcdc, 0x44bb48),
        },
    },
    'go': {   # the original has no Pause process: START opens Submenu
        'G': 0x351518, 'sys': 0x38538, 'stage_off': 0x3c, 'book': 'right',
        'stage_read': 0x4a858, 'stage_read_orig': 0x8e65003c,
        'area_read': 0x514c0, 'area_read_orig': 0x8e650040,
        'newgame_jal': 0x70184,
        'select_jal': 0x329d4,
        'proc': {
            'Area': (0x02f84c, 0x43b920), 'Ending': (0x033f60, 0x43bb30), 'Equip': (0x036690, 0x43c260),
            'GameOver': (0x03ba40, 0x43cc40), 'Ms': (0x03e37c, 0x4421c8), 'MsSave': (0x03ea04, 0x442530),
            'MsLoad': (0x03f3ac, 0x442900), 'Option': (0x0438dc, 0x442cf0), 'Play': (0x04a3bc, 0x4436c4),
            'Result': (0x04ce84, 0x443810), 'Stage': (0x051040, 0x443f54), 'StageSelect': (0x05235c, 0x444040),
            'Submenu': (0x055ddc, 0x444d90), 'SystemMenu': (0x063470, 0x4468a0), 'TimeOut': (0x06acf0, 0x447290),
            'Title': (0x06c2ec, 0x447398),
        },
    },
}


def boot(g):
    """Cold boot to the title's PRESS START, past the launcher and the no-save prompt."""
    s = g.s
    boot_to_intro(g)
    s.press('start', gap=120)    # skip the scroll to PRESS START
    s.press('start', gap=240)    # title menu


def new_game(g):
    """From the title menu to the lifestock choice, then confirm: NEW GAME path."""
    g.s.press('circle', gap=120); g.s.press('circle', gap=2)


def stage(st, ar):
    def go(g):
        boot(g)
        g.force_stage(st, ar)
        new_game(g)
        g.wait_proc('Area', 3000)
        g.wait(lambda: g.stage() == (st, ar), what='stage ids')
        g.s.run(300); g.s.press('circle', gap=300)
        g.unforce_stage()
    return go


STAGES = [(1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (3, 0), (3, 1), (3, 2), (4, 0), (4, 2)] + [(5, a) for a in range(9)] + [
    (6, 0), (7, 0), (8, 0), (9, 0), (0xa, 0), (0xb, 0)]


def overlay(proc, fields=(), st=1, ar=0, gap=150, mode=1):
    """Open PROC over a running stage: SELECT's jal SystemMenu calls it instead. Mode 1 pushes it; 2 replaces the stack,
    as the game does for Result."""
    def go(g):
        stage(st, ar)(g)
        g.redirect(g.a['select_jal'], proc, fields=fields)
        g.s.w32(g.mod(g.a['select_jal'] + 0x18), 0x34050000 | mode)    # ori a1,zero,mode before the store to sys+0xc
        g.s.press('select', gap=gap)
    return go


def from_title(proc, fields=(), a1=None, wait=600):
    """NEW GAME opens PROC instead of the game."""
    def go(g):
        boot(g)
        g.redirect(g.a['newgame_jal'], proc, a1=a1, fields=fields)
        new_game(g)
        g.wait_proc(proc)
        g.s.run(wait)
    return go


def title_menu(path, gap=60):
    """Real presses from the title menu; PATH is button names."""
    def go(g):
        boot(g)
        for b in path.split(): g.s.press(b, gap=gap)
    return go


def keys(base, path, gap=60):
    def go(g):
        base(g)
        for b in path.split(): g.s.press(b, gap=gap)
    return go


def scenes_for(game):
    d = {}
    for st, ar in STAGES:
        d[f'stage_{st:02x}{ar:02x}'] = dict(go=stage(st, ar), proc='Area', doc=f'stage {st:x} area {ar}')
    d['launcher'] = dict(go=lambda g: g.s.run(1800), doc='book screen')
    d['save_prompt'] = dict(go=to_save_prompt, doc='no save data prompt')
    d['title_intro'] = dict(go=lambda g: (boot_to_intro(g)), proc='Title', doc='red story scroll')
    d['title_menu'] = dict(go=boot, proc='Title', doc='NEW GAME menu')
    d['lifestock'] = dict(go=title_menu('circle'), proc='Title', doc='lifestock choice')
    d['load_game'] = dict(go=title_menu('down circle', 120), proc='Title', doc='LOAD GAME with no data')
    d['option'] = dict(go=title_menu('down down circle', 120), proc='Option', doc='options, first row')
    for i in range(1, 4):
        d[f'option_row{i}'] = dict(go=keys(title_menu('down down circle', 120), 'down ' * i), proc='Option', doc=f'options row {i}')
    d['button_config'] = dict(go=keys(title_menu('down down circle', 120), 'circle', 120), proc='Option', doc='button config')
    d['title_select'] = dict(go=title_menu('down down down circle', 120), doc='back to launcher prompt')
    d['pause'] = dict(go=lambda g: (stage(1, 0)(g), g.s.press('start', gap=60)), proc='Pause' if game == 're' else 'Submenu',
                      doc='START: PAUSE in Kai, sub screen in the original')
    for n in range(7):
        d[f'sysmenu{n}'] = dict(go=overlay('SystemMenu', [(0x140, n)]), proc='SystemMenu', doc=f'system menu variant {n}')
    d['gameover'] = dict(go=overlay('GameOver', gap=240), proc='GameOver', doc='GAME OVER')
    d['timeout'] = dict(go=overlay('TimeOut', gap=40), proc='TimeOut', doc='TIME OUT')
    d['result'] = dict(go=overlay('Result', [(0x100, 1)], gap=300, mode=2), proc='Result', doc='stage result')
    d['stage_select'] = dict(go=keys(overlay('SystemMenu', [(0x140, 4)]), 'circle left circle', 200), proc='StageSelect', doc='stage select')
    d['save'] = dict(go=save_screen, proc='MsLoad', doc='save list')
    d['witch'] = dict(go=lambda g: (stage(6, 0)(g), g.s.hold('right'), g.s.run(420), g.s.hold(''), g.s.run(420)), proc='Area', doc='witch message box')
    d['msg_all'] = dict(go=msg_all, proc='Area', doc='every stage message, in the witch box')
    d['save_fixture'] = dict(go=save_fixture, proc='MsLoad', doc='saves in game, keeps the file as work/saves/<game>')
    sav = f'work/saves/{game}'
    d['autoload'] = dict(go=lambda g: (g.s.run(1800), g.a['book'] and g.s.press(g.a['book'], gap=120), g.s.press('start'), g.s.run(300)),
                         sav=sav, doc='auto-load message (needs save_fixture first)')
    d['load_list'] = dict(go=load_menu, proc='Ms', sav=sav, doc='LOAD GAME with a save')
    d['load_done'] = dict(go=keys(load_menu, 'circle circle circle', 150), sav=sav, doc='load a save')
    d['movie_attract'] = dict(go=attract, proc='Title', doc='title left idle: opening movie mv00')
    d['movie_newgame'] = dict(go=lambda g: (boot(g), new_game(g), g.s.run(200)), proc='Title', doc='NEW GAME movie mv01')
    d['sub_tabs'] = dict(go=keys(lambda g: (stage(2, 1)(g), g.s.press('start', gap=40)), 'up right right right', 40), proc='Pause' if game == 're' else 'Submenu', doc='sub screen / pause')
    if game == 'go':
        d['sub_all'] = dict(go=sub_all, proc='Submenu', doc='every a03/a04 string in the sub screen detail pane')
    for n in range(3):
        d[f'ending{n}'] = dict(go=from_title('Ending', [(0xf0, n)], wait=1200), proc='Ending', doc=f'ending variant {n}')
    return d


def find_bytes(g, needle, lo=0x08c00000, hi=0x0a000000):
    """First RAM address holding NEEDLE; reads in 1 MB chunks with an overlap."""
    for a in range(lo, hi, 0x100000):
        i = g.s.rd(a, 0x100000 + len(needle)).find(needle)
        if i >= 0: return a + i
    raise LookupError('bytes not in RAM')


def point_string(g, addr, slot, d, i):
    """Make string SLOT of the .bms loaded at ADDR read string I of file bytes D: the bytes go to scratch RAM, and the
    u32 offset wraps backwards to it, so any length fits."""
    SCRATCH = 0x08801000
    n = struct.unpack_from('<I', d, 0)[0]
    a = struct.unpack_from('<I', d, 4 + i * 4)[0]
    b = struct.unpack_from('<I', d, 8 + i * 4)[0] if i + 1 < n else len(d)
    g.s.wr(SCRATCH, d[a:b] + b'\0\0')
    g.s.w32(addr + 4 + slot * 4, SCRATCH - addr)


WITCH_FRAMES = 840  # from stage 6 start, holding right for 420: the witch's box is up (fails the check if not)


def msg_all(g):
    """Every stage message (.bms strings the game only shows on rare story flags, tools/debug/README.md): in the witch's
    real box, copy string N to scratch RAM and point the slot she reads (s0600 string 11) at it.
    Text comes from work/<game>/pkdata, or BMS_DIR for a build; a shot per string in OUT/run/<scene>/."""
    stage(6, 0)(g)
    s = g.s
    root = os.environ.get('BMS_DIR') or f'work/{g.g}/pkdata'
    orig = open(f'{root}/s0600_stg.kpd/stage/s06/s0600/s0600.bms', 'rb').read()
    addr = find_bytes(g, orig[:64])
    s.r.save_state('work/states/_msg.ppst')
    ok = 0
    for st, ar in ((5, 6), (5, 7), (6, 0), (7, 0), (8, 0)):
        d = open(f'{root}/s{st:02x}{ar:02x}_stg.kpd/stage/s{st:02x}/s{st:02x}{ar:02x}/s{st:02x}{ar:02x}.bms', 'rb').read()
        n = struct.unpack_from('<I', d, 0)[0]
        for i in range(1, n):
            s.ws.call('game.state.load', path=os.path.abspath('work/states/_msg.ppst'), wait=True)
            s.r.base = s.ws.call('cpu.status')['us']; s.f = 0
            point_string(g, addr, 11, d, i)
            s.hold('right'); s.run(420); s.hold(''); s.run(WITCH_FRAMES - 420)
            s.shot(f'msg_s{st:02x}{ar:02x}_{i:02d}'); ok += 1
    s.hold('')
    print(f'{ok} message shots')


def save_route(g):
    """The original's variant 3 menu opens with the cursor on Stage Select; Kai's on Save."""
    return 'up circle circle circle' if g.g == 'go' else 'circle circle circle'


def save_screen(g):
    overlay('SystemMenu', [(0x140, 3)])(g)
    for b in save_route(g).split()[:-1]: g.s.press(b, gap=240)


def save_fixture(g):
    """Save through the game's own menu and dialog, keep what it wrote."""
    overlay('SystemMenu', [(0x140, 3)])(g)
    for b in save_route(g).split(): g.s.press(b, gap=240)
    src = os.path.join(g.s.ms, 'PSP', 'SAVEDATA')
    dst = f'work/saves/{g.g}'
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst)
    assert any(n.startswith('ULJM') for n in os.listdir(dst)), 'game wrote no save'


def load_menu(g):
    """With a save on the card: boot, autoload message, title menu, LOAD GAME."""
    s = g.s
    s.run(1800)
    if g.a['book']: s.press(g.a['book'], gap=120)
    s.press('start'); s.run(600); s.press('circle'); s.run(400); s.press('circle', gap=600)
    g.attach(); g.wait_proc('Title')
    s.press('start', gap=120); s.press('start', gap=240)
    s.press('down', gap=60); s.press('circle', gap=180)
    if g.g == 'go': s.press('circle', gap=180)   # past the save-icon picker on the title screen


def attract(g):
    boot_to_intro(g); g.s.press('start', gap=120)
    g.s.run(900)


def sub_all(g):
    """Every a03/a04 string in the knight-armor detail pane (real box, real font): the slot the pane reads for the
    armor's description points at each string in turn. A shot per string in OUT/run/<scene>/."""
    stage(2, 1)(g)
    s = g.s
    root = os.environ.get('BMS_DIR') or f'work/{g.g}/pkdata'
    a03 = open(f'{root}/play_res.kpd/2d/a03/a03.bms', 'rb').read()
    a04 = open(f'{root}/play_res.kpd/2d/a04/a04.bms', 'rb').read()
    addr = find_bytes(g, a03[:64])
    s.press('start', gap=40); s.press('circle', gap=40)   # armor detail open
    desc = 73    # a03 string: the knight armor's description
    s.press('cross', gap=20)
    done = 0
    for name, d in (('a03', a03), ('a04', a04)):
        n = struct.unpack_from('<I', d, 0)[0]
        for i in range(1, n):
            point_string(g, addr, desc, d, i)
            s.press('circle', gap=30); s.shot(f'{name}_{i:03d}'); s.press('cross', gap=12); done += 1
    print(f'{done} detail shots')


def to_save_prompt(g):
    s = g.s
    s.run(1800)
    if g.a['book']: s.press(g.a['book'], gap=120)
    s.press('start'); s.run(600); s.press('circle'); s.run(300)


def boot_to_intro(g):
    s = g.s
    to_save_prompt(g)
    s.press('left'); s.press('circle'); s.run(1000); g.attach(); g.wait_proc('Title'); s.run(100)


SCENES = {'re': scenes_for('re'), 'go': scenes_for('go')}
