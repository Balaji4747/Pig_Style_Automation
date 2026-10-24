# API samples

Real, verbatim captures from the live qa game session (23-24 Oct 2026). Not
fabricated/guessed — each file is exactly what the game returned.

- `init_response.json` — `POST /gs/pack-alpha/games/init` response.
- `spin_response.json` — `POST /gs/pack-alpha/games/spin` response (a
  no-win spin; `result.winLines` is `[]`).
- `spin_response_with_wins.json` — a complete winning spin (forced via
  `"6 OAK AA"`), `result.totalWin: 1.6`, 4 `winLines` entries. Used to
  validate `utils/megaways_calculator.evaluate()` — see below. No wild
  (WC) was involved in any of this spin's wins; a wild-involved complete
  sample hasn't been captured yet (two attempts timed out after the
  cheat-tool reload).
- `cheat_options.json` — `assets/panel/cheat.json`, the data behind the
  built-in cheat tool's forced-outcome list (`#cheatsContainer .cheatDiv`
  in `pages/cheat_panel.py`). Each key is an outcome label shown in the UI;
  the array is an internal per-reel seed the game uses to produce that
  outcome. Confirmed working: selecting `"3 OAK BN"` reliably landed exactly
  3 BN (Bonus) symbols on the next spin; `"6 OAK AA"` does not guarantee a
  6-of-a-kind AA win (the seed influences but doesn't fully determine the
  outcome — the captured sample's AA positions didn't actually line up,
  though it still produced other real wins used for validation).

## Calculator validation (`utils/megaways_calculator.py`)

`evaluate()` was run against `spin_response_with_wins.json` and reproduced
the server's 4 `winLines` **exactly** (symbol, count, positions, wildCount,
win amount) and matched `totalWin` (1.60 == 1.6). This empirically confirms:
bet scaling (`pay × bet/20`) and ways-counting-with-multiple-matches-per-reel
(reel 2 had 3 matching BB positions → exactly 3 separate winLine entries,
ways = 1×1×3 = 3). Wild substitution is *not* yet validated this way (no
wild-involved sample captured) — it's backed by the math file's wild weight
table + QA team notes (`OBS-02`/`OBS-04`) + standard Megaways convention
instead. The calculator intentionally has no max-win-cap logic — that's
RGS/server-side behavior, out of scope for a per-spin win-math oracle (see
`CLAUDE.md` > Win-calculation test oracle).

## No separate "cheat" spin request format

There is **no special spin request payload for forcing outcomes** — in
fact the spin request has **no body at all** (confirmed: `post_data` is
`None` on every captured spin request). Forcing an outcome works like this:
1. `window.cheatBtnClicked()` opens the cheat tool, `window.fetchCheatDetails()`
   populates it from `cheat_options.json`.
2. Selecting an option (`CheatPanel.select(text)`, a DOM click) **reloads
   the whole game session** — it is not read back on the next spin request;
   whatever seed it sets is server-side session state.
3. The first spin *after* that reload reflects the forced outcome. A normal
   `games/spin` call, same shape as `spin_response.json`.

See `pages/cheat_panel.py` and `GamePage.force_next_spin()`.
