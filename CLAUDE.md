# Pig Style — Test Automation Framework

## Overview
Pig Style is a 6-reel Megaways video slot for FEG (Fortuna Entertainment Group),
built by Pixentech. Up to 7 symbols per reel, up to 117,649 ways, wins pay for
3+ matching symbols on consecutive reels from the leftmost reel. This repo is
a Playwright + pytest UI/functional/math test automation framework for it,
driven by the QA workbook in `Docs/Pig_Style_QA_Test_Suite (1).xlsx` (561
test cases across 10 categories) and the game rules in
`Docs/Pig Style GR Eng 2.docx`.

## Architecture

### Canvas vs DOM — locator strategy
The game is **not** uniformly canvas-only. Confirmed live (23 Oct 2026):
- **Base game screen** (reels, spin/bet/menu/info/sound/turbo/buy controls):
  a single full-viewport `<canvas>`, **zero interactive DOM elements**,
  rendered with PIXI.js (`window.__PIXI_APP__`).
- **Info overlay** (Rules/Paytable/History, opened via the canvas Info
  button): **real DOM**, injected on top of the canvas, with rich
  `data-section`/`data-common`/`id` attributes. Use ordinary Playwright
  selectors here, not canvas coordinates (see `pages/rules_page.py`,
  `pages/paytable_page.py`).

For the canvas controls, buttons are clicked by their **live PIXI scene-graph
node name** (`BasePage.get_pixi_node` / `click_pixi_button`), not hardcoded
pixel coordinates — the bounds are read from the running game, so this
doesn't break if layout/assets change. This was explicitly chosen over
hardcoded coordinates after confirming the game exposes a stable, named scene
graph (`spinBtn`, `betBtn`, `menuBtn`, `infoBtn`, `turboBtn`, `soundOnBtn`/
`soundOffBtn`, `cheatBtn`, etc. — each uniquely named and reliable).

**Mobile/portrait, confirmed (24 Oct 2026):** the game serves a genuinely
different layout in portrait (controls stacked in a row below the reels,
not a scaled-down desktop view) — but the **exact same PIXI node names**,
just repositioned (e.g. `spinBtn` moves from `(1728, 463)` on a 1280x720
desktop viewport to `(148, 490)` on a 390x664 iPhone 13 viewport). Because
nothing is hardcoded, the PIXI-node click strategy, `expect_response`-based
waits, and Space-bar spin **all worked with zero code changes** — verified
end-to-end (load, spin, balance update) on an emulated iPhone 13. Run
against it with pytest-playwright's built-in device flag:
`pytest --env qa -m smoke --device "iPhone 13"` (see `fixtures/browser_fixtures.py`
— it defers to pytest-playwright's own device-based `browser_context_args`
instead of applying `config/env.yaml`'s desktop viewport when `--device` is
passed).

**Known exceptions / gotchas with the PIXI-node approach, found in testing:**
- **`startBtn` is ambiguous** — the game reuses this node name across
  multiple popups (splash "PLAY GAME", feature-intro screens, etc.), so
  "first visible startBtn" can match the wrong instance. `GamePage` does
  **not** use it; `dismiss_splash()` instead clicks a percentage-based
  canvas position (`PLAY_GAME_POSITION_PCT`, confirmed reliable) and
  confirms success via the unambiguous `splashView` node disappearing.
- **A node's `visible` flag + non-zero bounds does NOT mean "currently
  on screen and interactable."** `spinBtn` is present and reports
  visible/non-zero bounds even while the splash is showing on top of the
  (already-built) base game layer underneath. Don't use a control's own
  node as a "that screen is showing" signal — use a dedicated, scoped
  signal instead (e.g. `splashView` for the splash, `megawaysText` for
  "definitely on the base game").
- **Loading happens in (at least) two stages**: a generic platform loader
  first (`window.__PIXI_APP__` may not exist yet at all), then the Pig
  Style splash itself (which shows its own loading bar before "PLAY GAME"
  becomes clickable — clicking the loading-bar area does nothing). Always
  gate on `BasePage.is_pixi_ready()` before trusting any PIXI node query,
  and retry-click rather than click-once-and-hope.
- **The splash screen is sometimes skipped entirely** (session/preference
  dependent — likely tied to the init payload's `preferences.showIntro`).
  `GamePage.ensure_base_game_ready()` handles both cases: it waits for
  *either* the splash or the base game to appear, dismisses the splash only
  if present, then confirms the base game is actually ready via
  `megawaysText`. Always use `ensure_base_game_ready()` (wired into the
  `game_ready` fixture) rather than assuming the splash will appear.
- **Spin is triggered via the documented Space-bar shortcut**
  (`page.keyboard.press("Space")` after focusing the canvas), not a
  `click_pixi_button("spinBtn")` call. This is simpler and sidesteps any
  further click-precision edge cases on that particular button; all other
  controls (no keyboard equivalent) use the PIXI-node click.
- **A reused node name's "topmost" instance is the LAST match in document
  order, not the first** (confirmed 24 Oct 2026 against the real Auto Spin
  panel's `startBtn` vs. a stale decoy from an earlier popup) — PIXI draws
  children in array order, so later siblings render on top.
  `BasePage.get_pixi_node()` picks the last visible, non-zero-bounds match
  for this reason. For generic reusable components with no unique name at
  all (e.g. a "Buy bonus"/"Set"/"Cancel" button whose container is just
  `"btnText"`), use `click_pixi_text(exact_label)` /
  `get_pixi_text(node_name)` instead — matches by rendered text content,
  not pixel OCR.
- **The game ignores spin input while the previous round's win presentation
  (rollup/celebration) is still playing.** Back-to-back `spin()` calls
  timed out whenever the prior spin won anything. No PIXI node exposes
  "presentation done", and `wait_for_canvas_stable()` doesn't work here —
  there's a continuous ambient idle animation (drifting clouds etc.), so
  the canvas is never byte-identical between frames even at rest (confirmed:
  a 15s wait for stability never succeeded). `GamePage.spin()` instead
  waits a fixed `page.wait_for_timeout(3_000)` before pressing Space,
  calibrated against the confirmed `opCnf.spinDuration` (2000ms).
- **A "Please wait, loading feature game assets" overlay** (PIXI node
  `loader_anim`) can appear at any point — observed after playing a Free
  Spins round — and blocks spin input while showing, with the same
  stale-visible-flag issue (`megawaysText` still reports ready underneath
  it). `wait_for_loading_overlay_to_clear()` is called both in
  `ensure_base_game_ready()` and at the top of `spin()`.
- **A leftover unresolved round from a previous session (e.g. an
  unclosed Free Spins choice) persists server-side across page reloads.**
  The choice-screen popup itself fades in, so checking for it visually
  right after load is timing-sensitive and was confirmed unreliable (it
  can read as "not showing" before it's actually rendered). The init
  response's `unfinishedInfo` field is a reliable, immediate signal instead
  — `ensure_base_game_ready()` checks it and calls
  `resolve_pending_feature()` when non-null. `resolve_pending_feature()`
  itself doesn't gate on a single "is the choice screen visible" flag
  either (same staleness issue can affect it) — it just attempts each
  recovery step (pick Sticky Wilds if offered, dismiss any congrats popup,
  drain remaining feature spins, dismiss again) and tolerates steps that
  don't apply.
- **The win-presentation settle delay applies inside a Free Spins round
  too, not just between base-game spins** (fixed 25 Oct 2026, after a
  session got stuck for hours at "13 OUT OF 15 FREE SPINS" with a runaway
  balance). `play_feature_spins_to_completion()` used to press Space with
  no settle wait; a winning feature spin's next Space press was silently
  ignored mid-celebration, the `/feature` response never arrived, and the
  loop's own timeout made it look like "round complete" with spins still
  outstanding — and this repeated on every later recovery attempt, so the
  round could never actually drain. Fixed by adding the same
  `wait_for_loading_overlay_to_clear()` + 3s settle wait `spin()` uses,
  before each Space press in the loop.
- **The *final* free spin's win rollup can take noticeably longer to
  settle than a mid-round one** (stacked wild multipliers etc.) —
  `is_base_game_ready()` (`megawaysText`) reports ready while that last
  animation is still visually playing, so declaring the feature "resolved"
  as soon as the spin-completion loop ends is premature.
  `resolve_pending_feature()` now actively waits (10s) for the
  "Congratulations" popup to appear before dismissing it, falling back to
  one blanket 5s wait if a given feature variant shows no such popup.

### Network — source of truth for money/round data
Balance/bet/win/reels/ways come from the intercepted API responses
(`utils/network_spy.py`), **not** from canvas pixels or OCR. Real samples of
every endpoint below are in `docs/samples/` (verbatim captures, not
fabricated — see `docs/samples/README.md`). Confirmed live endpoints (qa
env, host `api.test.spiniq.io`):
- **Init**: `POST /gs/pack-alpha/games/init` — `data.playerInfo` (balance,
  min/max bet, currency, etc.), `data.gameInfo.payTable`.
- **Spin**: `POST /gs/pack-alpha/games/spin` — `data.roundId`, `data.closed`,
  `data.playerInfo.balance`, `data.result.{bet, betAmountUsed, totalWin,
  reelView, winLines, wildMultipliers, scatterCount, isFeatureTriggered,
  nextFeature, nextFeatureSubType, maxCapReached, maxWin}`.
- **Feature** (Free Spins round spins): `POST /gs/pack-alpha/games/feature`
  — same general shape as spin; not yet modelled (only discovered during
  recon; add a feature-result parser + `play_feature_spin()` when FS test
  cases are implemented).
- There is **no separate "ways" field** — ways = product of each reel's
  symbol count in `reelView` (confirmed: reel lengths 3,7,3,6,3,2 → 2268;
  all reels at 7 → 117649, matching the on-screen MEGAWAYS counter exactly).
  See `SpinResult.ways` / `utils/megaways_calculator.ways_count`.
- `result.betAmountUsed` = `bet / 20`, confirming the math file's per-way
  formula denominator (`Win = Bet x Pay/20 x Ways x product of wild
  multipliers`).

### Waits — no `time.sleep`, no polling where a direct wait exists
- `GamePage.goto()` and `GamePage.spin()` wait for their response via
  `NetworkSpy.wait_for_response(name, trigger)`, which wraps the triggering
  action in Playwright's `expect_response` — the wait is tied to the
  response caused by *that specific action*, not a poll of "has a matching
  response shown up yet in the capture log" (which could race with a stale
  response from an earlier action). `NetworkSpy.last()`/`.all()` remain
  available as a passive, continuously-recorded log for endpoints with no
  single triggering action to wrap (e.g. the Free Spins round's repeated
  `/feature` calls).
- `BasePage.wait_for(condition, timeout_ms)` polls a callable via
  `page.wait_for_timeout()` (Playwright's own wait, not `time.sleep`) — used
  for PIXI scene-graph state (no network signal available for those, e.g.
  "has the splash closed").
- `BasePage.wait_for_canvas_stable()` is a last-resort fallback for
  animations with no exposed "done" event (win rollups, reel-stop
  settling): polls canvas screenshots until consecutive captures are
  byte-identical. Prefer a specific signal (a response, a PIXI node
  appearing/disappearing) wherever one exists; reach for this only when none
  does.

### Typed API parsing (`utils/api_client.py`) and money handling
Raw init/spin JSON is parsed into frozen dataclasses (`InitResponse`,
`PlayerInfo`, `GameInfo`, `OpCnf`, `SpinResult`, `WinLine`) by
`parse_init_response()`/`parse_spin_response()`. `GamePage` uses these
internally (`get_init_data()`, `get_balance()`, `spin_and_wait()`) rather
than reading raw dicts.

**All money values (balance, bet, win, paytable entries, etc.) are
`decimal.Decimal`, never `float`** — converted via `Decimal(str(value))`,
never `Decimal(value)` directly on a JSON-parsed float, to avoid binary
floating-point rounding errors. Keep this convention in any new test code
that touches money: don't mix `Decimal` with `float` in comparisons/arithmetic
(it raises `TypeError`). Note `config/env.yaml`'s own numeric values
(`min_bet`, `max_bet`, etc.) are still plain YAML floats — wrap with
`Decimal(str(...))` at the point of comparison if asserting against a
`Decimal` from a parsed response.

The `init_data` fixture (`fixtures/game_fixtures.py`) exposes the parsed
`InitResponse` for the current session, so tests can assert against the
session's real paytable/bet-limits/RTP instead of hardcoding them:
```python
def test_something(init_data):
    assert init_data.player_info.min_bet == Decimal("0.1")
    assert init_data.game_info.pay_table["AA"][5] == Decimal("150")  # 6-OAK
```

### Win-calculation test oracle (`utils/megaways_calculator.py`)
`ways_count(reel_view)` is the confirmed ways formula (see above).
`evaluate(reel_view, paytable, bet_amount_used, multiplier=1)` reconstructs
every winning `Way` (symbol, count, positions, wild_count, win) the same way
the server's `winLines` does, for use as a test oracle (computed vs.
server-reported win). All money uses `Decimal` with `ROUND_HALF_UP` to 2
decimals (`money()`), matching the confirmed `opCnf.moneyRounding`.

**Validated against real data** (24 Oct 2026): run against
`docs/samples/spin_response_with_wins.json` (a complete, real winning spin),
`evaluate()` reproduced the server's 4 `winLines` **exactly** and matched
`totalWin`. This empirically confirms bet scaling and
ways-counting-with-multiple-matches-per-reel (a reel with 3 matching
positions produced exactly 3 separate winLine entries — one per way, as
the calculator computes via `itertools.product`). Cross-confirmed against
the math file: `BG Calc!K19` hardcodes `Bet=20`; the QA team's own
`OBS-04` states "wins are multiplied by the number of ways (product of
symbol counts per reel)".

**Not yet empirically validated**: wild (WC) substitution specifically —
no complete wild-involved winning sample has been captured (two attempts
timed out after the cheat-tool reload; see `docs/samples/README.md`). It's
backed instead by the math file's wild weight table (WC weight is 0 on
reels 1/6, non-zero on 2-5 — confirms reel scope) plus `OBS-02` and
standard Megaways convention. Revisit if a wild-involved sample surfaces.

**Deliberately out of scope**: no max-win-cap logic. The math file only
reports *uncapped* theoretical "Max Exposure" (up to 1,674,912 credits for
Buy FG2 — exceeding the live 250,000/`bbMaxWin` cap; `OBS-12` flagged this
as undefined). Cap enforcement is RGS/server-side behavior, not reproducible
client-side — test it via live/E2E assertions (force a near-cap win, check
the server truncates and credits correctly) rather than in this calculator.

**Confirmed: no cascade/tumble mechanic exists** — zero keyword hits across
all 19 sheets of the math file (`cascade`, `tumble`, `avalanche`, `respin`,
`roll`). This is a standard spin-and-stop Megaways game.

Remaining `ASSUMPTION`-tagged items in the module's docstring/comments
(e.g. all-wild-way payout, per-way vs. per-spin rounding order) weren't
exercised by the one validated sample (no wild involved, no fractional
rounding edge case) — still need checking before certification-grade use.

### Built-in QA cheat tool
The session has `allowCheat: true` (init payload), which enables a hidden
dev/QA cheat tool (`pages/cheat_panel.py`). Activation (all confirmed, not
guessed): `window.cheatBtnClicked()` opens it, `window.fetchCheatDetails()`
populates `#cheatsContainer .cheatDiv` from `assets/panel/cheat.json` with
named forced outcomes (`"3 OAK BN"`...`"6 OAK BN"` for bonus triggers,
`"<n> OAK WC"` for wild counts, `"<n> OAK <symbol>"` for specific paytable
lines, `"BIG WIN"`/`"MEGA WIN"`/`"GIGA WIN"`/`"UNBEL WIN"`/`"FEATURE_MISS"`/
`"NONE"`). **Selecting an option reloads the game session** (back to the
splash/loading flow) — the forced outcome applies on the first spin after
the reload, not immediately. Use `GamePage.force_next_spin(outcome)`.
This is the recommended way to deterministically hit P0 test cases that
need a specific trigger (e.g. `PS-FEA-001`: forced 3 BN trigger) instead of
relying on probability/retries. Verified end-to-end: selecting `"3 OAK BN"`
reliably landed exactly that many BN symbols on the forced spin.

### Config & paytable
- `config/env.yaml` holds per-environment settings (qa, staging): game URL,
  bet limits, timeouts, viewport (1280x720 — kept at 16:9 but small enough
  that the headed browser window, including its own chrome, fits on a normal
  screen), network URL patterns. No secrets — `GAME_URL`/`PLAYER_TOKEN` can
  be overridden from a local `.env` (gitignored, see `.env.example`).
- `config/paytable.yaml`: static paytable reference data, confirmed to
  exactly match the live init API's `payTable` shape (`[0, 0, 3-OAK, 4-OAK,
  5-OAK, 6-OAK]` credits at total bet 20). Loaded via
  `utils/paytable_loader.py`. Prefer the live `init_data` fixture's
  `game_info.pay_table` over this for anything that should reflect the
  actual running session rather than a static snapshot.

## Directory layout
```
config/      env.yaml, paytable.yaml (no secrets)
pages/       BasePage, GamePage, CheatPanel, PaytablePage, RulesPage, SettingsPage
fixtures/    browser/context setup, game_ready, init_data, network_spy
utils/       config_loader, logger, network_spy, canvas_helper, paytable_loader, api_client, megaways_calculator
tests/       ui/ functional/ math/ compatibility/ interruption/ recovery/ + test_smoke.py
reports/     screenshots, videos, traces, HTML report, allure results (gitignored)
Docs/        source game rules doc + QA test suite workbook (do not edit)
docs/samples/ real, verbatim init/spin/cheat-options API captures (see its README.md)
```

## Conventions
- Every test docstring includes the test case ID from the QA workbook (e.g.
  `PS-FUN-001`).
- Mark tests with the relevant pytest markers (`smoke`, `sanity`,
  `regression`, `ui`, `functional`, `math`, `compatibility`, `interruption`,
  `recovery`) — see `pytest.ini`.
- No locators/node names/coordinates/URLs in test files — only in `pages/`.
- Keep it simple: no speculative abstractions, no error handling for cases
  that can't occur.

## Confirmed game config (23 Oct 2026, from live init API + Rules panel)
- `minBet: 0.1`, `maxBet: 25`, `bbMaxBet: 2500`, `maxWin`/`bbMaxWin: 250000`
  — also independently confirmed via the live Rules panel's `#min-bet`,
  `#max-bet`, `#bb-max-bet`, `#max-win` text (resolves OBS-09).
- `defaultBet: 1`, fixed `possibleBets` list (not a continuous range).
- Currency: EUR, rounding: half-up to 2 decimals.
- RTP: 96.99% (`#rtp-value` in the Rules panel, matches math file's
  96.9886%).
- Buy Feature (FG1 = Raining Wilds): 100x bet. FG2 (Sticky Wilds) multiplier
  not present in the sampled init payload — still needs confirming.
- Wild multiplier can be x1, x2, or x3 (math-confirmed; rules text
  undercounts by omitting x1 — not a product bug, per client clarification).

## Open items
- OBS-02/03/04 (Wild symbol docs, win-evaluation wording, ways vs. payline
  language) — client said these would be clarified once the live game was
  available; now that we have it, worth a follow-up pass against the live
  Paytable tab content.
- FG2 (Sticky Wilds) buy-feature multiplier not yet confirmed live.
- `/gs/pack-alpha/games/feature` (Free Spins round spin) response not yet
  fully modelled in `GamePage`/`SpinResult` — only the base-game `/spin`
  path is implemented so far.
- SettingsPage (canvas `menuBtn`) trigger is confirmed but its internal
  panel content/selectors are not yet inspected.
- **Mobile/portrait splash position unverified.** The one hardcoded
  percentage fallback (`GamePage.PLAY_GAME_POSITION_PCT`, used only because
  `startBtn` is ambiguous) hasn't been confirmed against a real mobile
  splash screen — every mobile test run so far has landed on a session
  where the splash was already skipped (see shared-session caveat below),
  so it couldn't be triggered to check. `ensure_base_game_ready()` already
  handles "splash never appears" correctly either way, so this isn't
  currently blocking anything; revisit if mobile splash-specific test cases
  are added.
- **Shared test session caveat**: the qa `game_url`'s token identifies a
  specific player session server-side. Actions like forcing a cheat outcome
  or triggering Free Spins leave that session in a particular state (e.g.
  a pending "choose your Free Spins feature" screen) that **persists across
  page reloads** until resolved — it's server state, not just client UI
  state. If tests run concurrently or in sequence against the same token
  without resetting state, they can interfere with each other. Worth asking
  the team whether a fresh token/session can be issued per test run.

## Running tests
```
pip install -r requirements.txt
playwright install
pytest --env qa -m smoke
pytest --env qa -m "functional and not regression"
pytest --env staging tests/math -m math
```

## Reports
- HTML: `reports/report.html`
- Allure results: `reports/allure-results` (`allure serve reports/allure-results`)
- Screenshots/video/trace on failure: `reports/test-results/` (open traces
  with `playwright show-trace <trace.zip>`)
- Logs: `reports/logs/test_run.log`
