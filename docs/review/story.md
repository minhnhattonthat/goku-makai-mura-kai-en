# Story pass (phase 9)

Own fresh read-only pass (Orca worker, no subagents), `references/translation.md` §Review. Chapters from
`tools/chapters.py work/qa/story/chapters` (one per game: mv00-03, s0506-s0800, mv04-06 in play order); gate
`qa_gate.py check work/qa/story/manifest.tsv work/qa/story/verdicts`.

## Issues

### Critical
- mv00:3-7 (both games) - opening: Astaroth takes the princess, the royal blood makes the world the demon realm's, "you
  can't stop us" - the USA cut its text into 7 subtitles, but the game cues only mv00:1-5 (the attract run's `.bms`
  getter log fetches indices 0-5, never 6-7), so the English opening ended on "Once I, the dark lord, have begun".
  Fixed: USA wording re-cut into the JP's 5 subtitles; the last one ends "...nothing a mortal like you can do will stop
  me!" (the USA's "will hinder that which has been set into motion" shortened to fit 440 px x 2).

### Important
None.

### Minor (not filed: official USA text kept, D10/D13)
- s0600:1 / s0700:1 "If only you had..." vs s0800:1 "If only I had..." - the witch's point of view differs between
  lairs in the USA text; both read naturally.
- s0600-0800:3 "This is not enough, but it should do for now." - JP "not enough"; the USA's addition does not mislead.

## Assessment
re_story `fixed`, go_story `fixed` (the mv00 cut; everything else ok: voices consistent, each witch laugh maps to the
same JP laugh in every lair, names per `glossary.md`).
