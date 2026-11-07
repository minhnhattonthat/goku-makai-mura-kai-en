# Disc and archive layout

Parser: `tools/kpd.py` (`list`, `x`), test `tests/test_formats.py`. **Verified**: all three archives extract, nested ones too
(19,518 files from Kai's datapack alone). Every `.ana` parses and all 1,064 unique GIMs decode. Not yet proven by a rebuild.

## Disc (ULJM-05265, "極魔界村 改")

| Path | What |
|---|---|
| `PSP_GAME/SYSDIR/EBOOT.BIN` | Encrypted `~PSP` launcher. Nothing in it needs editing so far: every launcher text is in LAUNCHER.KPD. |
| `USRDIR/LAUNCHER/LAUNCHER.KPD` | Launcher graphics and sound (book screen). |
| `USRDIR/REGOKUMAKAI/` | **Goku Makaimura Kai**: `REGOKUMAKAI.PRX`, `datapack.kpd`, `movie/`, `module/`. |
| `USRDIR/GOKUMAKAI/` | **Goku Makaimura** (the original game, also on the disc): the same layout. **Both games are in scope.** |

`*.PRX` are **plain ELF** (`7F 45 4C 46`), not encrypted. They are loaded by the launcher, so byte edits are possible (not yet
tried on real hardware).

## DPLK ("KPD") format

Little-endian. `datapack.kpd` and LAUNCHER.KPD use alignment 0x800; the `*.kpd` nested inside `pkdata/` use 0x10, same format.

File header (0x10 bytes used, then padded to `root`):
`"DPLK"`, u32 0x100, then u64: `total_size`, `align`, `root` (offset of root dir), `dir_size`, `data_start`, `data_size`.

Directory block, at `hdr`:
- `u32 unknown` (0 or 1, not tied to having files), `u32 0x800`, u64 `ent_size`, u64 `ent_end`, u64 `sub_size`, u64 `data_off`, u64 `data_size`,
  u16 `count`, u16 align, u16 0x3e5 (997).
- From +0x36, 997 u16 hash buckets (0xffff empty) up to +0x800. Each record's +0x18 u16 is its chain link. The hash function is
  not worked out. It isn't needed while names don't change.
- `hdr+0x800`: `count` records of 0x80 bytes each.
- `hdr+ent_end`: child directory blocks, one after another.

Record: u64 `kind` (1 file, 0 directory), u64 `off`, u64 `size`, u16 chain, `name` at +0x1a (may hold `/`, e.g. `bgm/map.at3`).
- file: `off` is relative to the directory's `data_off`; absolute = `data_start + data_off + off`.
- directory: `off` is relative to the parent's child area; `size` is the subtree's directory bytes.

## Containers inside

- `.ana` = `@ANA` (`tools/ana.py`): u32 count at +0x10, entries at +0x20 of `{u32 off, u32 size, char name[8]}` (names cut at 8
  bytes, repeated). Every entry is a GIM.
- `.gim` = standard `MIG.00.1PSP`, but character textures store the palette block **before** the image block. The skill's
  `gim.py` assumed the reverse (patched copy: `tools/gim.py`; see `docs/skill-gotchas.md`).
- Only `.bms` carries text (`docs/re/text.md`). Others: `.at3` audio, `.pbd/.phd` sound banks, `.gmo` models, `ef*`/`es*`/`ss*` effects
  and scripts, stage data. A scan for Shift-JIS, UTF-8, UTF-16 and font codes found no text in them (`tools/survey_text.py`;
  hits were noise).

## Free space and the rebuild plan (phase 3; a plan, **not yet tested**)

- Same-size texture edits overwrite bytes in place: GIM re-encodes keep their size, and nothing moves.
- `.bms` grow, so the nested kpd holding them has to grow. Slack is small: nested padding is at most 0xF bytes, and outer padding
  under 0x800.
- Plan: rebuild the changed nested kpd, **append** it at the end of the outer data area, then repoint that one record's `off` and
  `size` and update `total_size`/`data_size`. Hash tables and names stay untouched.
- ISO room: `GOKUMAKAI/datapack.kpd` (LBA 21280) sits right before `GOKUMAKAI.PRX` (LBA 135024); `REGOKUMAKAI/datapack.kpd`
  (LBA 249760) right before `module/` and `movie/`. `iso9660.patch` relocates a file that outgrows its slot, which would copy a
  234 MB archive. Moving the small neighbour (the PRX, or `module/` plus `mv00.pmf`) to the end of the image instead frees 5-15 MB
  behind each datapack, enough to grow it in place. Needs a small extension of `tools/iso9660.py`.
- `xdelta3 -B <image size>` at release, because of the moved files.
