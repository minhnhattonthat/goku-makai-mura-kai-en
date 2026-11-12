# Reverse-engineering notes

One file per subsystem. Findings are marked verified (with how) or guess (with why).

- `kpd.md`: disc layout (launcher plus two games), DPLK archives, ANA and GIM, free space, rebuild plan.
- `text.md`: `.bms` format, font encoding, control codes, PRX strings.
- `boxes.md`: every text box's width and line budget in the variable-width font (the width gate), glyph torture line.
- `graphics.md`: every Japanese texture, per screen.
- `usa.md`: the USA disc (D10): which of its files carry English text, font and art for reuse.

Prior work: no fan patch or tools for this game found (web search, 2026-11-08). The official English release of the original game
is *Ultimate Ghosts 'n Goblins* (PSP, 2006); Kai never left Japan. The disc's `a70` ending lines and the movie credits are already English.
