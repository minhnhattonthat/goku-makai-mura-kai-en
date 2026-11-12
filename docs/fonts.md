# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| `font/jfont_00.gim`, `font/jfont_00.bft` (both games' datapacks) | the USA disc *Ultimate Ghosts 'n Goblins* (ULUS-10105), `USRDIR/datapack.kpd`; the player supplies it (D10) | Capcom's | not as a file: the patch is a diff against the Japanese disc, so it carries the changed bytes. Phase 9 decides whether the patch needs the USA disc as a second input instead. | all game text | bft rects trimmed to the ink (`tools/vwf.py`, D11); the sheet is unchanged |
