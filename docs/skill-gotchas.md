# Skill gotchas

One line each: the reference it belongs in, then the fact.

- `scripts/gim.py` (fix stranded in `tools/gim.py`): `walk()` only attaches a palette to an image that came first; this game's character GIMs store the palette block first, so 325 of 1,064 textures failed with `'NoneType' object is not subscriptable`. Keep a pending palette for the next image.
- `references/setup.md`: `fetch_emu.py ppsspp` failed with `CERTIFICATE_VERIFY_FAILED` on this Windows Python; `SSL_CERT_FILE=$(python -c "import certifi;print(certifi.where())")` fixes it.
- `scripts/iso9660.py`: its CLI has no usage text; `x` needs three arguments (`x ISO OUTDIR`) and `patch()` can only move the file that grew, not a smaller neighbour (`docs/re/kpd.md`).
- `SKILL.md` Tools table: `sheet.py` does not take texture PNGs by directory (it wants `f<frame>.png`), so texture contact sheets needed a separate labelled, deduping script (`tools/gimsheet.py`).
