# Graphics-text survey

Static sweep done: all 1,064 unique game GIMs (`tools/sweep_gim.py`: 0 undecodable, none skipped) plus the launcher's ANAs, read on
contact sheets (`tools/gimsheet.py`), plus sampled frames of the 17 PMFs of REGOKUMAKAI. The tour half (screens reached in the
emulator) comes with the phase 5 marker build. Regenerate: `tools/ana.py x`, `tools/gimsheet.py`.

ID = `<ana>/<index>_<name>` as dumped by `tools/ana.py`. Same ID in both games unless marked. An ANA is one file per game, so each
game's copy gets written.

Reachability of the rows marked "demo leftover" is unproven. They come from a "Capcom Special Demo 3 in 1" launcher.

## Must translate

| ID | Screen | Japanese | Notes |
|---|---|---|---|
| a60/20_op_w_00 | Title intro story | 16 lines, red | Same text, redraw once, write to both games |
| a60/27_op_w_01 | Save-carryover notice | 5 lines + logo | re only? check; refers to the disc titles |
| a60/14,15_tit_w_1 | Load menu | 極魔界村 (ULJM-xxxxx / 05147) | Two sizes per texture |
| a10/02_op_wor0 | Options header | オプション ボタンコンフィグ | |
| a10/05,06_op_wor0 | Options rows | ボタンコンフィグ BGM音量 SE音量 デフォルト | |
| a10/18_op_wor0 | Button functions | re: 魔力 魔力 使用しない 魔力 ジャンプ 攻撃; go: 魔力装備 盾装備 ワープスピア 魔力 ジャンプ 攻撃 | **Differs per game** |
| a10/19_op_wor0 | Config footer | デフォルト △○×□ オプションへ戻る L R | |
| a10/20_op_wor0 | Button legend | 移動 カーソル移動 システムメニュー 決定 戻る + re: ポーズ / go: サブ画面 | **Differs per game** |
| a02/00_sy_wor0 | Pause menu | ロード タイトル オプション セーブ ステージセレクト 次のステージへ コンティニュー | |
| a30/00_stse_w0 | Stage select | ステージセレクト | |
| a30/01_stse_w0 | Stage select | ステージ + digits | |
| a30/05_b_word0 | Stage select | 決定 戻る 再生 | |
| a06/00_door_w0, a50/08_door_w0 | Loading | 次へ (NOW LOADING is English) | Game and launcher copies |
| go a03/03-09_sub_w0x | Sub screen (original game only) | Stage names, 状態 盾 魔力 アイテム ワープスピア 装備 解除 次のページ トップページ 魔力 Lv. リセット etc. | Dense 256x64 atlases; UV layout must be read before redrawing |
| s0a0001mazo (texture) | Stage 0a | 仮 scratched on the stone | A dev "temporary" mark; inpaint it |

## Logos (brief: keep the Japanese logo only if no official English version exists)

The original game has an official English title, **Ultimate Ghosts 'n Goblins**; Kai has none. These rows need a redraw or a call:

| ID | Where |
|---|---|
| a60/03_logo_go, a60/13_tit_ico | Title screen, load icons |
| a60/22,24,25,26 + 23 改 seal | Kai seal over the logo (re) |
| la a50/00_lau_a00 | Book screen logos (coloured + sepia) |
| memstick sl_ico01,03 (PNG), PSP_GAME ICON0/PIC0 | Save icon, XMB |
| a10/15,16_op_psp0 | Logo inside the options PSP drawing |
| mv00.pmf, last seconds | **Burned into the movie**; can't change without re-encoding PSMF |

## Demo leftovers (launcher; translate if reachable, otherwise waive)

| ID | Japanese |
|---|---|
| la a80/00_word00 | "This software's titles are in development..." disclaimer, 4 lines |
| la a83/00_word02 | カプコン スペシャル体験版 3in1 splash |
| la a84/00-02_back_* | Long blurbs for the three demo titles |
| la a84/05_icon_ca | Katakana Capcom Classics Collection logo |
| la a84/11_word, a84/12_yesno | このゲームを起動しますか? ... / はい いいえ 戻る 決定 |

## Keep as is

- Already English: a60 menu labels (NEW GAME, LOAD GAME, ARCADE MODE...), PRESS START BUTTON, a00 SCORE/TIME/GAME OVER/TIME OUT, a40 TOTAL
  SCORE, a70 THE END and "Congratulations for Complete / You are Great Player" (the original's own English), NOW LOADING, NO DATA.
- la a82/00 CERO mark: a ratings mark, not text.
- PMF credits are in English. Story subtitles are `.bms` overlays, not burned in (mv00-mv06). No other Japanese seen in the sampled
  frames of mv01-mv0b and select00-04. mv00, mv04 and mv06 differ per game; only REGOKUMAKAI's were sampled, so sample the GOKUMAKAI
  copies in phase 8.
