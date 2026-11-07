# Skill gotchas

One line each: the reference it belongs in, then the fact.

- `scripts/gim.py` (fix stranded in `tools/gim.py`): `walk()` only attaches a palette to an image that came first; this game's character GIMs store the palette block first, so 325 of 1,064 textures failed with `'NoneType' object is not subscriptable`. Keep a pending palette for the next image.
- `references/setup.md`: `fetch_emu.py ppsspp` failed with `CERTIFICATE_VERIFY_FAILED` on this Windows Python; `SSL_CERT_FILE=$(python -c "import certifi;print(certifi.where())")` fixes it.
- `scripts/iso9660.py`: its CLI has no usage text; `x` needs three arguments (`x ISO OUTDIR`) and `patch()` can only move the file that grew, not a smaller neighbour (`docs/re/kpd.md`).
- `SKILL.md` Tools table: `sheet.py` does not take texture PNGs by directory (it wants `f<frame>.png`), so texture contact sheets needed a separate labelled, deduping script (`tools/gimsheet.py`).
- `scripts/psp.py` (worked around in `tools/debug/pspsession.py`): `WS.recv` does `json.loads` on every frame, so a raw Shift-JIS log event raises `UnicodeDecodeError`, and it ignores opcode 8: a WebSocket close (the emulator exiting) surfaces as a decode error on bytes `03 e9`. Handle op 8 and decode with errors='replace'.
- `references/emulator-qa.md` §PPSSPP: on PPSSPPHeadless `cpu.resume` drops the debugger connection; `cpu.runUntilTime` is the only way to run, and it did not stop at a `cpu.breakpoint.add` breakpoint in my test, so code breakpoints gave no caller traces. `memory.write {address, base64}` works on code too (the new instruction ran), so RAM patches at safe points are the usable hook.
- `references/emulator-qa.md` §Debug tool: PSP warp pattern that worked: find the process factories, then redirect one `jal` through a stub in free RAM (0x08800100), no ROM patch. Rare text: copy a string to scratch RAM and wrap the table's u32 offset backwards to it, in any real text box.
- `SKILL.md`: `sheet.py DIR` wants `f<frame>.png`; pass explicit PNG paths for named shots, and it writes `sheet.png` beside the first file, so an old sheet there gets replaced.
- `references/emulator-qa.md` §PPSSPP: PPSSPPHeadless exits on a game SIGSEGV; psp.py only sees the closed socket (a decode error on `03 e9`), but `ppsspp.log` holds the faulting PC and MIPS call stack. Read it before guessing.
- `references/emulator-qa.md` §Debug tool: forcing a menu over a live stage can skip the resource state the real flow sets up; a process that crashes when pushed may work when it replaces the stack (mode 2), as the real flow does.
