# Visual-QA reviewer brief - Goku Makaimura Kai (both games)

You review shots and contact sheets from a translated build's QA tour and give each one a verdict. Read-only on
everything except your one verdict file: no edits to the repo, no git, no subagents.

## Inputs (in your dispatch)
- A chunk file: one `id<TAB>path` line per sheet. Read every sheet in it; none may be skipped.
- Your verdict file: `work/qa/verdicts/<chunk>.tsv`.
- The original disc's shots: `work/qa/warp/<game>_<scene>.png` (same names, phase 2, Japanese) and `glossary.md`.

## How to look
- Read each sheet whole first. Where text is small, zoom into it with
  `python -X utf8 $SKILL/scripts/sheet.py SHEET.png --crop x,y,w,h --zoom 3 --out <scratch>.png` and read that.
- When something looks wrong, open the same id from `work/qa/warp/` (`sheet.py EN.png --compare JP.png`). If the
  original shows the same thing, it is the game's own behaviour: `ok`, with a note.
- Zoom into every Yes/No prompt, selection box, menu row and speech bubble: a few pixels of misalignment don't show
  at sheet scale. To measure one: `python -X utf8 $SKILL/scripts/inkbox.py SHOT.png x,y,w,h`.

## Judge
An `issue` is any of:
- Japanese still visible;
- text overflowing a box, clipped by a frame, or running off screen;
- text off-centre where the original centres it: an option in its selection box or cursor brackets, a label, a bubble;
- garbage tiles, wrong or missing glyphs, a strike or stray pixels across letters;
- broken line breaks: a word split mid-line, a page ending mid-sentence, a one-word last line;
- an empty box where text belongs;
- a name that differs from `glossary.md`.

Standing non-bugs, `ok`:
- text still typing out, a box mid-fade or mid-scroll, a cursor caught mid-blink;
- a map or scene still loading after a warp;
- anything identical in the original's shot.
- Kai's Japanese logo (title, 改 seal, book screen, save icons) and the standalone disc's save icon: kept on purpose
  (D5, `docs/re/graphics.md`). The original game's logo is the USA English one.
- The PSP system save/load dialog's own labels (Back, Enter, Load completed) follow the console language; the save
  details inside it are game text. A save made by the Japanese disc shows its Japanese title there.
- The circle/cross button icons are the Japanese ones on purpose (OK is circle in this game).
- `msg_all`, `memstick_all`, `sub_all` shots show strings forced into one box (the witch's, the no-save prompt, the
  sub-screen pane): judge the text and its fit, not whether that box is the string's usual one.
