# Text boxes: the width gate (phase 5)

Every budget is in font px of the variable-width font (`tools/vwf.py`): glyph advance = the bft `w`, and the game draws the
font at 1:1 on the 480x272 screen. `tools/lint.py` checks every line against these (`tests/test_insert.py` runs it), and
`vwf.line_widths` gives any line's width. Measured 2026-11-12 with `build.py --marker ruler` (every text run replaced by
`(id) A123456789B123456789...`) on both games, shots in `work/qa/ruler/`; the last glyph drawn before the wrap or the
edge gives the width of that prefix.

**The engine wraps by itself** at a box's width, mid-word (the ruler continued on the next line). The USA text breaks its
lines by hand (`\n`) inside the budget, and so must we: the lint fails any line over budget.

| Box | Files | Width per line | Lines | Measured how |
|---|---|---|---|---|
| Help / menu box | a02 (system menu), s0506-s0800 (stage and witch messages) | 412 | 2 | measured: a 412 px prefix stays on the line, 421 wraps (re/go sysmenu0, witch). |
| Help box with button icons | a10 (options), a30 (stage select) | line 1: 412, line 2: 300 | 2 | measured: line 2 shares its row with the circle/cross icons from x 335; text starts at x 33 (option, stage_select). JP help text sits on line 2 (`\n` first); the USA text uses line 1. |
| Subtitles | mv00-mv06 | 440 | 2 | measured: the block is centred on its longest line (`{c:02}`), no box; the wrap is wider than the screen (733 fits), so the budget is the screen less 20 px a side. |
| Memory-stick prompts | memstick | 440 | 15 | measured: block-centred, no box, no wrap seen before the screen edge; blank lines place it vertically. go string 11 has 15 lines (14 `{c:02}` rows, 9 with text, then a trailing break) and draws them all, 18 px apart, its last text row at y 225 with room below (`work/qa/marker/run/go_memstick_all/mem_11.png`). re string 11 is cut at the sides in the shot. |
| Equipment pane | a03, a04 (original game: item text, warp prompts) | 182 | 8 per page | measured: name and description both wrap at 182-189 (go:sub_all on the ruler build, a03 index 73). `{06}` starts a new page. a04 (warp staff prompts) draws in this pane too (go:sub_all a04 shots, phase 8 QA): the engine wraps mid-word there ("Witc/h Lair"), so a04 is broken by hand. |
| Save dialog | prx.json | `max` bytes (UTF-8) | | the PSP system dialog; a longer string moves to free slot space in the region (`script.prx_patch`), so the limit is the region's free space (lint fails when none is left); the Shift-JIS new-data title has no pointer and keeps its 15-byte slot. |

Choice lines (`{c:01}{05}YES  {05}NO`) are the USA's on every prompt and need no new budget.

The official USA text fits every box with the variable-width font (lint: 0 warnings).

## Glyph torture line

`build.py --marker torture` puts every glyph the font has (`script.TORTURE`) in every box. re:sysmenu0, 2026-11-12: every
letter, digit and mark draws cleanly, double spaces show, `™` and `★` too (`work/qa/torture/`). The font has no
`[ ] { } < > @ ^ _ \` \\ | ~ $`; the lint fails a line that uses one.
