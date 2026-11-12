"""Text coverage inputs for the skill's textcover.py (PPSSPP has no Lua probe, so the logs come from warp runs).

    python -X utf8 tools/cover.py [--tour work/qa/tour] [--out work/qa/cover]
    python -X utf8 "$(python tools/skill.py)/scripts/textcover.py" work/qa/cover work/qa/cover/strings.tsv --waive docs/text_unshown.tsv

Writes OUT/strings.tsv (`<game>:<id>` and a made-up hex key per non-empty string of script/) and one OUT/<run>/log.txt of
`TEXT <key>` lines per tour run dir, from two sources:
- textlog.txt, written by warp.py: a log-only breakpoint on the `.bms` getter (tools/debug/README.md) records the file's
  string count, its last offset word, the index read and the file's first 64 bytes in RAM, which name the file among
  the build's unpacked `.bms` (work/goku_en/<game>/pkdata).
- the forcing scenes (msg_all, memstick_all, sub_all) point one slot at each string in turn, so the getter only sees the
  slot: their shot names (msg_s0600_03, mem_04, a03_112) give the ids instead, one shot per string drawn in the real box.
"""
import argparse, glob, json, os, re, struct
from collections import defaultdict

FORCED = {'msg_all': re.compile(r'msg_(s\d{4})_(\d+)\.png$'), 'memstick_all': re.compile(r'(mem)_(\d+)\.png$'),
          'sub_all': re.compile(r'(a0[34])_(\d+)\.png$')}


def strings():
    out = []
    for p in sorted(glob.glob('script/*/*.json')):
        d = json.load(open(p, encoding='utf8'))
        out += [f"{d['game']}:{r['id']}" for r in d['strings'] if r['jp']]
    return out


def bms_index(root):
    """(count, last offset word) -> [(stem, first 64 bytes)], for every .bms under ROOT."""
    idx = defaultdict(list)
    for p in glob.glob(f'{root}/**/*.bms', recursive=True):
        d = open(p, 'rb').read()
        n = struct.unpack_from('<I', d)[0]
        idx[(n, struct.unpack_from('<I', d, 4 * n)[0])].append((os.path.basename(p)[:-4], d[:64]))
    return idx


def files_for(idx, n, last, head):
    """Stems whose file starts with the RAM bytes seen at the getter's bms (identical files, e.g. mv02/mv03, give both)."""
    ram = bytes.fromhex(head) if head != '-' else b''
    return {stem for stem, d in idx.get((n, last), ()) if ram.startswith(d)}


def run_ids(run, game, idx):
    scene = os.path.basename(run)[3:]
    if scene in FORCED:
        ids = set()
        for f in os.listdir(run):
            m = FORCED[scene].search(f)
            if m: ids.add(f"{game}:{'memstick' if m[1] == 'mem' else m[1]}:{int(m[2])}")
        return ids
    ids = set()
    p = os.path.join(run, 'textlog.txt')
    for line in open(p, encoding='utf8') if os.path.exists(p) else ():
        _, n, last, i, head = line.split()   # TEXT count last index head, hex
        for stem in files_for(idx, int(n, 16), int(last, 16), head):
            ids.add(f'{game}:{stem}:{int(i, 16)}')
    return ids


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tour', default='work/qa/tour'); ap.add_argument('--out', default='work/qa/cover')
    a = ap.parse_args()
    ids = strings(); key = {s: f'{i:x}' for i, s in enumerate(ids)}
    os.makedirs(a.out, exist_ok=True)
    with open(f'{a.out}/strings.tsv', 'w', encoding='utf8', newline='\n') as f:
        f.writelines(f'{s}\t{key[s]}\n' for s in ids)
    idx = {g: bms_index(os.environ.get('BMS_DIR_' + g.upper()) or f'work/goku_en/{g}/pkdata') for g in ('re', 'go')}
    seen = set()
    for run in sorted(glob.glob(f'{a.tour}/run/[rg][eo]_*')):
        g = os.path.basename(run)[:2]
        got = run_ids(run, g, idx[g]) & key.keys()
        seen |= got
        os.makedirs(f'{a.out}/{os.path.basename(run)}', exist_ok=True)
        with open(f'{a.out}/{os.path.basename(run)}/log.txt', 'w', newline='\n') as f:
            f.writelines(f'TEXT {key[s]}\n' for s in sorted(got))
    print(f'{len(ids)} strings, {len(seen)} shown in {a.tour}/run')


if __name__ == '__main__':
    main()
