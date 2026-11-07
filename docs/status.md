# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool next (Step 0 and phase 1 done). Last build: none yet.
- **Done:** Repo set up: dump pinned, hooks, check, emulator, tools. Recon: the disc is a launcher plus two games (Kai and the original), plain-ELF PRX, DPLK and ANA formats parsed, `.bms` text fully decoded with `tbl/jp.tbl`, graphics survey static half done. See `docs/re/`.
- **Next:** Phase 2: `tools/debug/` warps from a cold boot via PPSSPP's WebSocket (`memory.write`, `psp.py`) or CWCheat, for both games. List: launcher, title, options, button config, load/save, stage select, every stage including the bosses and witch rooms, pause menu, sub screen (original only), result, game over, every movie, ending, credits. RAM addresses are unknown; find them with `ramsearch.py` and the PRX's symbols (`GameOverExec` etc. are in the binary). Then phase 3 per the plan in `docs/re/kpd.md`.
- **Open bugs:** none.
- **Waiting on the user:** Non-blocking: (1) D9 assumes both games are in scope. (2) The Japanese logo: official English exists for the original (*Ultimate Ghosts 'n Goblins*), so the brief wants it replaced, but no official art is in the repo and Kai has no English logo. Default: redraw a matching English logo in phase 7, leave the logo burned into `mv00.pmf`. (3) Launcher demo leftovers (`docs/re/graphics.md`): default is to translate if reachable, else waive. (4) Keyboard input in the windowed PPSSPP (`tools/ppsspp/`) wasn't tried, because headless agents can't press keys; scripted input is proven.
