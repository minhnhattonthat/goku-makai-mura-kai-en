# Glossary - Goku Makaimura Kai

Binding for every translator and reviewer. Agents propose additions in reports; only the controller edits this file.

## Rulings (asked of the user once; options and reasons in docs/decisions.md)
- Honorifics: kept. Name order: Western, given name first.
- Romanisation source: official English names (*Ultimate Ghosts 'n Goblins*, the English enemy names in mv04-mv06 credits) where they exist, else an earlier fan patch, else Hepburn without macrons.
- Credits: English.
- Register / flavour: the USA text's (D10): plain, slightly archaic for witches and the narrator ("shall", "begone", "Behold"), no contractions in narration. Sound effects: none in the text.
- Abbreviations: full names and terms everywhere, prefer engine changes over shortening.
- Game titles (D12): the original game is *Ultimate Ghosts 'n Goblins* (box-art spelling, space before 'n; the USA memstick text writes "Ghosts'n", left as is); Kai is *Ultimate Ghosts 'n Goblins Kai*.

## Style rules
- Punctuation map: 「」 -> "...", 『』 -> '...', … and ・・・ -> ..., ！？ -> !?, fullwidth digits and － -> ASCII (1-1).
- Lines are broken by hand (`\n`) inside the box budget (`docs/re/boxes.md`); `python -X utf8 tools/lint.py -v` is the gate.
- The font has no `[ ] { } < > @ ^ _ \` \\ | ~ $`.
- Witches: haughty, archaic imperatives ("Take this and begone!", "Behold..."). Their laughs follow the USA s0600:7-10.
- Save-dialog strings (`prx.json`) are UTF-8 in the PSP system font, ASCII only, within `max` bytes.

## Characters
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| アーサー | Arthur | | | |
| プリンセス | the princess | | | |
| 大魔王 | Dark Astaroth | | stage-5 boss (USA a03 art, credits) | Astaroth alone except where a slot forces it (prx:0x349da8, phase 7) |
| 暗黒魔王 | the dark lord / Hades | | "dark lord" in story text (USA mv04:12), Hades as a name (credits, Hades' Chamber) | Demon King |
| 魔女 | witch | | | |

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 暗黒魔界 | the Demon Realm | | USA s0507 | Dark Demon World |
| 魔女の棲家 / 棲み家 | Witch Lair (Red/Yellow/Blue Rose Witch Lair) | | USA a03/a04 | Witch's House |
| 第Nの魔界門 | First/Second/Third/Fourth Demon Gate | | USA a03 art | |
| 1-1 魔の森 .. 隠された火炎の滝 | stage names as the USA a03 sub-screen art: 1-1 Magic Forest, 1-2 Bloody Nest, 2-1 Storm Fortress, 2-2 Death Castle, 3-1 Rotten Swamp, 3-2 Sea of Death, 4 Scorch Mountain, 5 Black Palace, Dark Astaroth's Chamber, Hades' Chamber, Unknown Tower, Forgotten Dungeon, Hidden Firefall | | `script/go/prx.json` | |

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 光の力 | Light Rings | | USA s0506/s0507 | |
| 最強の力 | the "Ultimate Power" | | Kai s0507 (the Demon Realm's entry condition) | same family: 最強の魔力 (s0600/0700/0800:12, the witches) = "the Ultimate Power" |
| 魔力 | magic / Magic Power | | Magic Power in the a03 stat panes | |
| 魔力水晶 | Magic Crystal | | "<Name> Magic Crystal", USA a03:143-151 | |
| 爆発の魔力 | Flare Magic | | USA a03:36 | Explosion Magic |
| メモリースティック | Memory Stick Duo™ | | USA memstick | |

## Decisions from earlier batches
- phase 6 (37 new rows, translated by the controller) 極魔界村セーブデータ -> Ultimate Ghosts 'n Goblins (Save Data cut to fit the 31-byte slot)
- phase 6 大魔王の部屋 -> Astaroth's Chamber for now (slot 19 bytes); phase 7 repoints it to restore Dark Astaroth's Chamber
- phase 6 memstick:11 (go) keeps the jp's ★ placeholder for the Kai disc and its icon
