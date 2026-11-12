Goku Makaimura Kai (PSP) - English fan translation v{version}
==============================================================

Unofficial English patch for the Japanese PSP disc Goku Makaimura Kai (ULJM-05265). The disc holds two games and
both are translated:
- Goku Makaimura Kai -> "Ultimate Ghosts 'n Goblins Kai" (all text in English)
- the original Goku Makaimura -> "Ultimate Ghosts 'n Goblins" (the official USA English text, font and title art)

No game data is included; you need your own dump of the Japanese disc. Do not share patched images.

What you need
-------------
Base image (Redump: "Goku Makai-Mura Kai (Japan)", ULJM 05265):
  file    Goku Makai-Mura Kai (Japan).iso
  size    978485248 bytes
  CRC32   DE3C4590
  MD5     7e8b15544d205838b92cb5217c1a414f
  SHA-1   574ce2a6b04ac99a8e246051767b1f8ef8dc2efc
The USA disc is NOT needed: the English font and art the patch uses are inside it.

How to patch
------------
xdelta3 (command line):
  xdelta3 -d -s "Goku Makai-Mura Kai (Japan).iso" {patch} "Goku Makaimura Kai (English).iso"
Or a GUI front-end such as Delta Patcher: original file = the Japanese ISO, patch = {patch}.

Patched image:
  size    {size} bytes
  CRC32   {crc32}
  SHA-1   {sha1}

Playing
-------
Tested in PPSSPP v1.20.4. Start from a cold boot (no savestates made with the Japanese disc: they keep the old text
and font). OK is circle, cancel is cross.
On the book screen press START, then circle, to boot a game.

Translation status
------------------
- Story subtitles, stage messages, item and magic descriptions, menus, save and memory-stick messages: English.
- Title menus and graphics with text: English. Kai keeps its Japanese logo (no official English logo exists for it);
  the logo burned into the opening movie stays as it is.
Known issues: none known. Report bugs on the project's GitHub issues page, a save or screenshot helps.

Credits
-------
Original game (c) CAPCOM. English text of the original game: Capcom's official USA release (Ultimate Ghosts 'n
Goblins); the Kai-only text is new. This project is not affiliated with Capcom.
The translation and tools were made with extensive AI assistance (Claude by Anthropic). Corrections are welcome.
