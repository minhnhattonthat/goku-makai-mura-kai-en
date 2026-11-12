# Polish pass

Minor review findings, deferred to one pass before release. One line each: `- [ ] id - note`; tick `[x]` when fixed or
`waived: reason`. The release script refuses to run while any line is unticked.

- [x] go/a03:142 - review (phase 6, codex): "Range expands with increased Magic Power Lv." omits that power rises too (爆発範囲と威力がアップ). fixed: a03:142 and a03:103 now "Range and power increase with Magic Power Lv." (D13).
- [ ] memstick:11 (both games) and prx titles - "Ghosts 'n Goblins" vs the official memstick rows' "Ghosts'n Goblins" on sibling prompts: pick one spelling (D12).
- [ ] phase-7 review Minor 5 - "no other reader" of moved PRX strings is a comment (`script.py` PRX_PTRS); add a test scanning the original PRX for words and lui+addiu/ori/load pairs into vacated slots (reviewer's scan found 0 today).
- [ ] phase-7 review Minor 4d - no negative test for diffcheck's Japanese-left and archive-member branches (table-word case added).
- [ ] go/memstick:11 - keeps the jp ★ placeholders ("Ultimate Ghosts 'n Goblins ★" disc); phase 8: if real play reaches it, say "Kai" (D12), else waive.
