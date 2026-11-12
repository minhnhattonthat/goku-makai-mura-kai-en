# The USA disc (*Ultimate Ghosts 'n Goblins*, ULUS-10105)

`rom/Ultimate Ghosts 'n Goblins (USA).iso`, SHA-1 `0b569d1b415abb328fa2bf0bdaea7832b075feac`. The owner supplied it to reuse its
English text and graphics (D10). It holds only the original game: no launcher, no Kai. Unpacked to `work/us_iso`, `work/us`
(`tools/iso9660.py x`, `tools/kpd.py x`).

Layout (verified, 2026-11-12): game code is in an encrypted `SYSDIR/EBOOT.BIN` (no `GOKUMAKAI.PRX`), `USRDIR/datapack.kpd`
is the same DPLK format with the same tree as `GOKUMAKAI/datapack.kpd`. 19,359 files against 19,364: the USA one lacks
`k000065.efp` and item `k0830` (4 files). Movies mv00-mv07 and select00-04 only (no mv08-mv0b).

Files that differ from `work/go` (everything else is byte-identical):

| What | Files | Use |
|---|---|---|
| Text | 18 `.bms`: memstick, mv00-06, a02, a03, a04, a10, a30, stage messages | Official English for every shared string. Decodes with `tbl/jp.tbl` except glyphs the USA font remaps (`Ⓚ` in memstick reads as "KB"): make a USA table from its bft in phase 4. |
| Font | `font/jfont_00.bft`, `font/jfont_00.gim` | The English font and its widths: candidate for the phase 5 font decision. |
| Textures | 8 `.ana`: a00, a02, a03, a10 (play_res), a06 (loading), a30 (st_select), a60 (title), a70 (ending) | English texture art, drop-in for the original game; a start for Kai's (a10 differs per game). |
| Layouts | 5 `.csl` beside a03, a06, a10, a30, a60 | Sprite rects for the English art: copy with the matching `.ana`. |
| Save icons | 3 `memstick/sl_ico0*.png` | English save icons. |
| Other | 10 `.lgc`, one each `.cll .gmk .gcl .gmo`, `k0000.efa/.epl` | Stage and player data, likely bug fixes; not text. Leave alone unless a phase needs them. |

Plan: original game takes the USA files (bms, font, ana+csl) where the tree matches; Kai reuses USA strings and art for whatever
it shares with the original, and only Kai-only text and art gets a new translation.
