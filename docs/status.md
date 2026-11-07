# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool nearly done: 125 of 127 scenes pass, 2 open (Next). Last build: none yet.
- **Done:** Repo set up: dump pinned, hooks, check, emulator, tools. Recon: the disc is a launcher plus two games (Kai and the original), plain-ELF PRX, DPLK and ANA formats parsed, `.bms` text fully decoded with `tbl/jp.tbl`, graphics survey static half done. See `docs/re/`. Debug tool: `tools/debug/warp.py` (`tools/debug/README.md`): every Kai scene and all 26 stages of both games warp from a cold boot; save fixtures in `work/saves/` (gitignored; rebuild with `save_fixture`).
- **Next:** Finish phase 2, then phase 3 per the plan in `docs/re/kpd.md`.
  1. `go:stage_select`: the emulator exits after the real menu route that works in Kai. The WebSocket close surfaces as a `JSONDecodeError`.
  2. `go:msg_all`: the emulator exits on the first string, though `go:witch` passes. Suspect the original's getter or box dislikes `point_string`'s wrapped offset, or its s0600 box doesn't read string 11; try a forward offset, or check which string it reads. `go:sub_all` uses the same trick and passes.
  3. `go:autoload` passes but its shot is black: timing, the book press shifts it. Find the frame.
  4. Review still owed: `work/qa/warp/` shots weren't all read. Read: both games' stages, Kai menus, Kai `msg_all` first sheet, `go` sub screen and system menu sheets. Not read: `go:sub_all`'s 209 detail shots, `go` ending and option sheet 1. A pass means the process check held, not that the picture is right.
  5. Not reached, listed in `tools/debug/README.md`: mv02/mv03 subtitles, `memstick.bms` error strings, the real door trigger in 5-6 and 5-7, god mode.
- **Open bugs:** none in the game. Phase 4: `tbl/jp.tbl` misreads some kanji: 必 comes out 父 (父要 for 必要), 心 comes out 必 (必配 for 心配), 揃 comes out 捕 (捕う for 揃う). Check the table against the font sheet before extracting.
- **Waiting on the user:** Non-blocking: (1) D9 assumes both games are in scope. (2) The Japanese logo: official English exists for the original (*Ultimate Ghosts 'n Goblins*), so the brief wants it replaced, but no official art is in the repo and Kai has no English logo. Default: redraw a matching English logo in phase 7, leave the logo burned into `mv00.pmf`. (3) Launcher demo leftovers (`docs/re/graphics.md`): default is to translate if reachable, else waive. (4) Keyboard input in the windowed PPSSPP (`tools/ppsspp/`) wasn't tried, because headless agents can't press keys; scripted input is proven.
