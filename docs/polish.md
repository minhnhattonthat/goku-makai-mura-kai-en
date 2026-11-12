# Polish pass

Minor review findings, deferred to one pass before release. One line each: `- [ ] id - note`; tick `[x]` when fixed or
`waived: reason`. The release script refuses to run while any line is unticked.

- [x] go/a03:142 - review (phase 6, codex): "Range expands with increased Magic Power Lv." omits that power rises too (爆発範囲と威力がアップ). fixed: a03:142 and a03:103 now "Range and power increase with Magic Power Lv." (D13).
- [x] memstick:11 (both games) and prx titles - "Ghosts 'n Goblins" vs the official memstick rows' "Ghosts'n Goblins" on sibling prompts: pick one spelling (D12). fixed: go memstick:3 now "Ghosts 'n" (the only "Ghosts'n" left), phase 8.
- [x] a02/a30/a04 choice rows (`{c:01}{05}YES  {05}...NO  `) - phase-8 QA: the choice cursor sits ~22 px left of YES (JP: ~7 px from はい), `re_sysmenu5`; NO's margin matches the JP. Cursor x likely from a fixed-width measure of the row; memstick rows (full-width space between) look right. Find the cursor placement or waive. fixed: the cursor x is fixed at the JP's; rows respaced so YES/NO sit where はい/いいえ do (`docs/re/boxes.md`), worse case found too: NO's cursor drew across YES in the real a30 prompt.
- [ ] phase-7 review Minor 5 - "no other reader" of moved PRX strings is a comment (`script.py` PRX_PTRS); add a test scanning the original PRX for words and lui+addiu/ori/load pairs into vacated slots (reviewer's scan found 0 today).
- [ ] phase-7 review Minor 4d - no negative test for diffcheck's Japanese-left and archive-member branches (table-word case added).
- [ ] go/a03 (descriptions) - phase-8 QA: the USA wrapped for its 12 px fixed font, so with the VWF lines run short and ~40 pages end on a one-word line that fits above ("succumbed to / evil.", `stubs` scan in the phase-8 session). Readable, natural wrapping in a narrow pane; rewrap by tool or waive.
- [ ] go/memstick:11 - keeps the jp ★ placeholders ("Ultimate Ghosts 'n Goblins ★" disc); phase 8: if real play reaches it, say "Kai" (D12), else waive.
