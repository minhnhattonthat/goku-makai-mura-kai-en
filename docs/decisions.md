# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-11-08 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western order, given name first. Project default from the owner's one-shot brief. |
| D2 | 2026-11-08 | Romanization source for names | official art, earlier patch, Hepburn | Official English names where they exist, else an earlier fan patch, else Hepburn without macrons. From the brief. |
| D3 | 2026-11-08 | Credits | stay Japanese, translate | English. From the brief. The movie credits are already English. |
| D4 | 2026-11-08 | Abbreviations | engine work first (default), abbreviate | Engine work first, the skill default; the brief didn't override it. |
| D5 | 2026-11-08 | Graphics text left in Japanese | none (default), list | Translate all of it (titles, menus, banners, cards). Leave the original Japanese logo only if it has no official English version. From the brief. |
| D6 | 2026-11-08 | Specs and plans | need approval, pre-approved | Pre-approved: keep going through every checkpoint. From the brief. |
| D7 | 2026-11-08 | Existing saves or savestates | supply, none | None provided; build the debug tool as usual. From the brief. |
| D8 | 2026-11-08 | Release and publishing | | Never run `gh release create`, never change repo visibility; the run ends at a built and verified release zip. Commit and push to main at each phase end. From the brief. |
| D9 | 2026-11-08 | Scope: the disc holds Kai and the original game | Kai only, both | Both, plus the launcher. Agent default under "translate this game": a player can pick either from the launcher, and most assets are shared. The owner can narrow this. |
