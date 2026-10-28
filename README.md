# Pig Style Test Automation

Playwright + pytest test automation for the Pig Style Megaways slot (FEG).

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
playwright install
cp .env.example .env            # fill in GAME_URL / PLAYER_TOKEN
```

## Running tests
Select environment with `--env` (`qa` default, or `staging`):
```bash
pytest --env qa -m smoke
pytest --env qa -m functional
pytest --env qa tests/math -m math
pytest --env qa -m regression
pytest --env qa -n auto             # parallel (pytest-xdist)
pytest --env qa --reruns 2          # retry flaky tests
pytest --env qa -m smoke --device "iPhone 13"   # mobile/portrait emulation
```

## Viewing reports
- **HTML report:** open `reports/report.html` in a browser.
- **Allure report:** `allure serve reports/allure-results`
- **Screenshots/video/trace (on failure):** `reports/test-results/`.
  View a trace with:
  ```bash
  playwright show-trace reports/test-results/<test-name>/trace.zip
  ```
- **Logs:** `reports/logs/test_run.log`

## Functional Test Coverage (`tests/functional/`)

40 tests across 13 files, covering the core player-facing game behavior end
to end against the live game (real spins, real purchases — no mocking).
Every test is tagged with its QA workbook test case ID (`PS-FUN-xxx`) for
traceability. Where the built-in cheat/force-outcome tool is used, it's only
to reliably trigger a scenario (e.g. a real Buy Feature purchase to enter
Free Spins) — the cheat tool for forcing specific reel outcomes was found to
be unreliable in this environment and has been removed from this suite;
results are always validated against what the game's API actually returns,
never assumed.

| File | Tests | What it covers |
|---|---|---|
| `test_game_launch.py` | 2 | Game loads into a correct, playable state (right starting bet/balance); the splash screen dismisses properly into the base game when shown |
| `test_base_game.py` | 3 | Reel count/height stay within the game's 2-7 symbol range; the on-screen MEGAWAYS ways counter always matches the math; the maximum 117,649 ways displays correctly when all 6 reels are full |
| `test_balance.py` | 3 | Balance is debited/credited by exactly the right amount every spin; a real win is credited and matches independent recalculation; the on-screen balance always matches the server's balance |
| `test_bet.py` | 5 | Bet panel shows correct min/max and leaves bet unchanged on cancel; every configured bet level is selectable; bet stays within min/max; bet is retained across spins; bet controls are correctly disabled mid-spin and during Free Spins |
| `test_turbo.py` | 1 | Turbo Spin mode doesn't alter results or balance math |
| `test_auto_spin.py` | 4 | Auto Spin plays exactly the selected number of rounds and stops; Stop ends it after the current round; Cancel starts nothing and debits nothing; bet controls are disabled during Auto Spin |
| `test_wild.py` | 2 | Wild symbol only ever appears on reels 2-5; Wild correctly substitutes for paying symbols in the actual win calculation (verified against an independent win-calculator, not just assumed) |
| `test_win_evaluation.py` | 2 | The game's entire win-evaluation algorithm (left-to-right matching, ways multiplication, no double-paying, summing multiple wins) is verified by independently recalculating real spin results and comparing exactly; paytable payouts strictly increase with more matching symbols |
| `test_paytable_scaling.py` | 2 | Real spin payouts match the documented formula (bet × credits ÷ 20) at min/default/max bet; the Paytable info screen shows the mathematically correct, correctly-rounded value for **every symbol and every payout tier, at all 38 configured bet levels** |
| `test_bonus_symbol.py` | 3 | 3+ Bonus symbols reliably trigger Free Spins; fewer than 3 never do; the Bonus symbol itself never pays out as a regular win |
| `test_free_spins.py` | 2 | The Free Spins choice screen offers the correct number of spins for each mode; Free Spins play at the bet that triggered them with no additional debits |
| `test_buy_free_spins.py` | 9 | Full "Buy Feature" purchase flow: cost always shown correctly and scales with bet; cancelling takes no money; confirming debits the exact cost once and reliably starts the feature; winnings aren't double-counted; your bet setting survives the feature; both Sticky Wilds and Raining Wilds are reachable and play correctly when purchased |
| `test_history_panel.py` | 2 | The in-game History screen correctly records a recent round's bet/win; a purchased Free Spins round is correctly recorded with its cost and identified as a purchase |

## Running the functional suite
```bash
pytest --env qa tests/functional -v                       # all 40, Chromium
pytest --env qa tests/functional -v --browser-channel msedge   # all 40, Microsoft Edge
pytest --env qa tests/functional/test_wild.py -v           # a single file
pytest --env qa tests/functional -m sanity -v              # just the sanity-tagged subset
```
Add `--headed` to any command above to watch it run in a visible browser.

## Project docs
See [CLAUDE.md](CLAUDE.md) for architecture, conventions, and current open
items. Source documents (game rules, QA test suite workbook, math file) are
in `Docs/` — do not edit, they are the source of truth for test case IDs
and expected values.
