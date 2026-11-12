# Debug tool

`warp.py` reaches any scene from a cold boot, in either game (`re` = Kai, `go` = the original). It pokes RAM over PPSSPP's
debugger only; no disc file changes, so it runs on the original ISO or a build (`--iso`), and nothing of it ships.

    python -X utf8 tools/debug/warp.py --list
    python -X utf8 tools/debug/warp.py re:stage_0201 --out work/qa/warp
    python -X utf8 tools/debug/warp.py --all [--game re] [--only stage] [--skip stage_0] --out work/qa/warp
    python -X utf8 tools/debug/warp.py go:stage_0600 --keys "right*300 circle" --every 30 --tail 600   exploring

Output: `OUT/<game>_<scene>.png`, a state in `work/states/<game>_<scene>.ppst`, exit 1 if a scene's process isn't in the live chain.
`--all` regenerates everything (about 35 minutes for both games). Run after any engine, font or graphics change, because states
carry old code. `autoload`, `load_list` and `load_done` need `save_fixture` first: `--all` runs it in the right order.

## How the game is built

Addresses are for the unmodified PRXes. **If a build moves PRX code, `attach()` fails on purpose: redo the table in `scenes.py`**
with `prxtrans.py` (transitions, factories, static objects), `prxmap.py` (dis, xref, names) and `prxfunc.py` (who calls, fields).

| | Kai (`re`) | Original (`go`) |
|---|---|---|
| Module base | 0x08804000 | same |
| G, singleton pointer | module 0x351098 | module 0x351518 |
| Stage / area ids | G+0x40 / +0x44 | G+0x3c / +0x40 |
| Process manager `sys` | G+0x38578 | G+0x38538 |
| Player pointer (x,y,z floats at +0xd0) | G+0x37780 | G+0x37740 |

- Each screen is a static `Process` object made by a factory. A transition stores a mode in `sys+0xc` and the object in `sys+0x10`.
  Modes: 1 push over the current one, 2 replace the stack, 3 used by NEW GAME.
- `sys+0x14` heads the live list, linked through object +0 (`Game.chain()`). The scene check reads this, not a frame count.
- `0x301fcc` (Kai) is the `.bms` string getter: `(bms*, index)`, and it spins forever on an index past the count.

## The tricks

- `force_stage`: NEW GAME loads whatever the two read instructions give, so they become `ori a1,zero,id` until the stage is up.
  Writing the ids to RAM doesn't work: Play resets them.
- `redirect`: writes a stub at 0x08800100 and points one `jal factory` at it, optionally storing fields in the returned object.
  Sites: title NEW GAME (mode 3) and SELECT in a stage (mode 1, or 2 by patching the `ori` at site+0x18).
- `msg_all`, `sub_all`: rare strings shown in a real box. `point_string` copies string N to scratch RAM (0x08801000) and wraps the
  `.bms` offset slot backwards to it, so length doesn't matter. Set `BMS_DIR` to the build's unpacked `pkdata` to check translated text.

## Scene notes

- SYSTEM variants (`SystemMenu+0x140`): 0, 1 stage menu; 2 game over; 3 after a stage; 4 with stage select; 5, 6 open on the save prompt.
- `Result+0x100`: 1 is the tally, 0 skips straight to SystemMenu. Opening Result from the title closes the emulator, so it goes
  through SELECT with mode 2. `Ending+0xf0`: 0, 1, 2 play mv04, mv05, mv06, then credits.
- StageSelect forced from the title is black; the real menu route works, so the scene uses that. It runs SystemMenu with mode 2,
  as after a real clear: over a live Area the original null-reads resource 0x30 (`0x53a04`) and the emulator exits.
- PPSSPPHeadless exits on a game SIGSEGV. The MIPS stack is in `OUT/run/<scene>/ppsspp.log`; warp reports it as a `JSONDecodeError`.
- The witch reads s0600 string 11 in Kai, string 1 in the original (`witch_slot`). Its file there stops at 10.
- Result plays mv03 when `Result+0x100` is 0 and the two ids after the live ones are 5, 7 (`movie_boss1/2`, one scene per subtitle).
- The memstick prompt lays out its text once, so `memstick_all` sets the slot before it opens. Autoload's message holds about 120 frames.
- The door messages in stages 5-6 and 5-7 didn't fire on pressing up at the door, trigger not found: `msg_all` shows them in the
  witch's box. The real trigger is still unknown, and the door's own layout is unproven.
- `go:carryover`: the original game looks for saves of the standalone disc (ULJM05147, in its PRX; Kai doesn't). A copy of
  the save fixture with its PARAM.SFO directory renamed to `ULJM05147DATA00` passes (`scenes.carryover_sav`), so the boot
  shows the a60 op_w_01 notice and LOAD GAME offers a second icon.
- Teleport: write the player's x. A warp into enemies kills Arthur; there is no god mode yet.

## Not reached

- `mv02` as a movie: only `0x4da98` plays movies from Result and it asks for mv03. `mv02.bms` is byte-identical to `mv03.bms`.
  `mv07.pmf` has no subtitle file.
- Real faults behind the memstick errors: `memstick_all` shows those strings in the no-save prompt instead. String 11 clips at the
  sides there; its real screen is unproven.
- God mode: not built, phase 8 adds it if a playtest needs it. A dump of the player object's first 0x1000 bytes across one hit showed no obvious HP field; that was one run, not proof.
- `a02` strings only some menu states use: see phase 8. `a03`, `a04` show in the detail pane, not always their own screen.
- Launcher demo leftovers (`docs/re/graphics.md`): no route found, still undecided.
