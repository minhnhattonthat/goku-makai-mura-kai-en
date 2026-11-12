# Goku Makaimura Kai English translation

Unofficial English fan translation of **Goku Makaimura Kai** (PSP, Capcom, 2007; ULJM-05265): the source text and
tools that build the patch. The disc holds two games and both are translated: *Goku Makaimura Kai* as
*Ultimate Ghosts 'n Goblins Kai*, and the original *Goku Makaimura* as *Ultimate Ghosts 'n Goblins*, with Capcom's
official USA English text, font and title art.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a save or
a screenshot helps most.

## Translation status

| Part | Status |
|---|---|
| Story subtitles (opening, endings), stage and door messages | Translated |
| Menus, item / weapon / magic descriptions, save and memory-stick messages, save-dialog titles | Translated |
| Title menus, sub-screen tabs, stage cards and other graphics with text | Translated; Kai keeps its Japanese logo (no official English one exists), and the logo burned into the opening movie stays |
| Credits roll | Already English in the original |

A scan of every text file in the built disc finds no Japanese left. Known issues: none known, see
[Issues](../../issues).

## Patching

Base image: `Goku Makai-Mura Kai (Japan).iso` ([Redump](http://redump.org/discs/quicksearch/ULJM%2005265/), ULJM 05265)

| | Size | CRC32 | MD5 | SHA-1 |
|---|---|---|---|---|
| Japanese ISO | 978485248 | DE3C4590 | 7e8b15544d205838b92cb5217c1a414f | 574ce2a6b04ac99a8e246051767b1f8ef8dc2efc |
| Patched ISO (v1.0) | 1211432960 | 60A35A25 | 17e53227b2143a6e09e1691eaf7bb0dc | 2de3473fb530acd1142516e5a861ce4bc50806f1 |

Apply the release's `.xdelta` with xdelta3 (`xdelta3 -d -s "Goku Makai-Mura Kai (Japan).iso" PATCH.xdelta out.iso`)
or Delta Patcher. The USA disc is not needed. Tested in PPSSPP v1.20.4; start from a cold boot, since savestates made
with the Japanese disc keep its old text and font. On the launcher's book screen press START, then circle.

## What's here

| Path | What it is |
|---|---|
| `script/re/`, `script/go/` | Every text block of Kai and of the original game: Japanese, official USA English, final English. Fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: unpack, insert, lint, diff check, release; `tools/debug/` warps to any scene in the emulator. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.claude/agents/` | Subagent types (translator, reviewer, visual QA, playtester) with only the tools each needs. |

## Build your own patched ISO

Needs Python 3.12+, your own dump of the Japanese disc, and the USA disc *Ultimate Ghosts 'n Goblins* (ULUS-10105),
whose English text, font and art the build reads.

```sh
git clone https://github.com/minhnhattonthat/goku-makai-mura-kai-en
cd goku-makai-mura-kai-en
# copy your dumps to rom/ (names, SHA-1s: rom.sha1; the build refuses any other dump):
#   rom/Goku Makai-Mura Kai (Japan).iso            978485248 bytes, SHA-1 574ce2a6b04ac99a8e246051767b1f8ef8dc2efc
#   rom/Ultimate Ghosts 'n Goblins (USA).iso       SHA-1 0b569d1b415abb328fa2bf0bdaea7832b075feac
python -X utf8 tools/build.py                          # -> build/goku_en.iso
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text and the official USA English text in `script/` are
Capcom's and are included only so the translation can be checked against them. Goku Makaimura Kai and Ultimate Ghosts
'n Goblins are (c) Capcom; this project is not affiliated with Capcom. Do not share patched images.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
