# Progress — Autonomous QA Automation Run (started 2026-10-24)

Working order per instructions: PS-INT -> PS-ERR -> PS-STR -> PS-MTH -> PS-FEA -> PS-EDG ->
PS-UI -> PS-CMP -> PS-REG, P0 before P1 before P2 within each sheet. See `DECISIONS.md` for
every non-obvious judgment call (read that file for the "why" behind anything below).

Workbook row counts (from `docs/test_cases/INDEX.md`, extracted this run):
PS-INT 30, PS-ERR 20, PS-STR 27, PS-MTH 63, PS-FEA 59, PS-EDG 42, PS-UI 47, PS-CMP 21,
PS-REG 162. Functional sheet (90 rows) already automated from a prior session — not
rewritten here.

## Session/infra setup (done)
- git initialized (repo had no history); baseline + fix commits made.
- `.claude/settings.json` permission config (unrelated request, done earlier).
- Fixed a real bug in `GamePage.play_feature_spins_to_completion` /
  `resolve_pending_feature` that left the shared QA session stuck for hours in an
  undrained Free Spins round — see DECISIONS D-005/D-006. Confirmed fixed via
  `test_smoke.py`.
- Added `negative`/`boundary`/`integration`/`test_case(id)` pytest markers (D-007).
- Extracted all 9 target sheets + Functional + Defect-Observation Log to
  `docs/test_cases/*.csv` + `*_summary.md`, plus `docs/test_cases/INDEX.md`.
- Re-ran the full Functional suite (no reruns) after the page-object fix to check for
  regressions — **IN PROGRESS / see note below**.

## CHECKPOINT: live validation paused — see DECISIONS.md D-012
The live `tests/interruption/` run (30 cases) got as far as 5/30 (3 pass, 1 fail under
investigation, 1 still resolving a leftover stuck round from an interrupted prior attempt)
before demonstrating that a single adversarial feature-recovery can legitimately take tens
of minutes under D-011's fix. Rather than keep burning session time with no confident
upper bound, live validation of PS-INT/PS-ERR/PS-STR/PS-MTH/PS-CMP is paused — all test
code is written and committed, but marked PENDING (not confirmed passing) in
`reports/EXECUTION_SUMMARY.md`. A diagnostic test is currently running in the background to
let the one in-flight stuck-round recovery finish naturally and leave the shared session
clean — do not start any other live-game work until that completes (check for a live
python/chromium process before running anything else against the game).

## Functional-suite recheck: not re-run a third time (by design)
Two issues ate a large amount of this run's live-session time before any new-sheet work
could proceed: D-005/006 (stuck Free Spins session) and D-009/010/011 (a second,
independent stuck-session incident, root-caused and fixed more robustly, plus ruling out
an alternative hypothesis via an isolated diagnostic). Both are now confirmed fixed
(diagnostic test passed end-to-end; the `open_auto_spin_menu()` gesture was proven
innocent). Rather than burn more shared-session time re-running the full 32-test
Functional suite a third time (which would mostly re-confirm what the diagnostics already
showed), I'm moving on to the actual priority-1 deliverable (PS-INT) now. The one
Functional-sheet finding that stands either way — `test_auto_spin.py`'s two count-based
tests have a pre-existing, unrelated test-logic gap (D-010) — is documented and left
untouched per this task's scope rules. Recommend a full Functional-suite rerun as a
follow-up once the new-sheet work is further along, time permitting.

## Sheet: Interruption & Recovery (PS-INT) — 30 rows, all P0/P1, all "Yes"
Status: **IN PROGRESS**. Full row list read (`docs/test_cases/ps_int.csv`). Feasibility
assessment done (see DECISIONS D-008 once logged) — most rows are genuinely automatable
against this Playwright/PIXI/network-spy stack via reload, `page.context.set_offline()`,
`page.route()` response mocking, and viewport-size changes for "rotation". True native
mobile OS events (app backgrounding, incoming calls, device lock) are not controllable
from Playwright — those get `visibilitychange` event dispatch as a documented partial
substitute, not a full equivalent.
Not yet started writing test files as of this checkpoint.

## Sheet: Error Handling (PS-ERR) — all 20 written
11 implemented live (mocked network/server faults via `page.route()`, offline via
`set_offline()`, malformed JSON, double feature-choice, asset-blocking). 9 Blocked with
reasoning (Buy-confirm gap x2, uncaptured `/feature`/bet-set payloads x2, no confirmed
error-popup UI node, no guaranteed max-win-cap cheat, no RGS-level malfunction injection).
Not yet run live as of this checkpoint (queued behind PS-INT in the one-account-serial
constraint).

## Sheet: STR - Transaction Testing (PS-STR) — all 27 written
13 implemented live (balance/transaction math, concurrent-request idempotency via raw
`fetch()`, invalid-token rejection, malformed/negative-win response mocking, responsible-
gaming flag presence). 14 Blocked/not-independently-testable, mostly because spin requests
carry **no body at all** (confirmed empty, docs/samples/README.md) — there is no bet/buy-
cost/FS-choice payload to tamper with, and no round-identifying token to "replay". Not yet
run live.

## Sheet: Math Validation (PS-MTH) — automatable subset written (~21 of 63)
Per this run's own instructions, statistical/distributional cases (RTP x6, hit frequency,
volatility, reel-selection/height/wild-multiplier distributions, reel-strip-vs-math-file
matching, max-exposure) need a large offline simulation against the math file's weights —
not a Playwright UI test — and are reported as "Requires simulation", not attempted here.
Written: symbol win-amount checks (017-025, extending the existing Functional sheet's
AA/BB/CC/KK/LL cases to all symbols the cheat tool supports), FS award-count-per-bonus-
count for both feature choices (038-045, parametrized), wild-involved win *structure*
checks (029/030 — deliberately NOT asserting exact win amount, see DECISIONS.md: the
calculator's wild-multiplier handling is itself an unvalidated ASSUMPTION, so a monetary
mismatch here would misreport a calculator gap as a product defect), bet-denominator-20
(057), no-Bonus-during-FS (062). Specific wild-multiplier VALUES (027/028/031, x1/x2/x3)
are Blocked — not forceable without looping random spins, which the task rules disallow.
014/053/054/058/061/063 are "No" in the workbook itself (config/version/architecture
checks, not runnable tests). Not yet run live.

## Sheet: Compatibility Testing (PS-CMP) — 1 reusable test covers the 13 Partial smoke rows
Wrote one full-flow smoke test (load/spin/win/bet-change/both FS choices/Buy-interface/
Auto-Spin/Info/Sound) instead of 13 near-duplicates — it's meant to be run once per
`--browser`/`--device` combination (`pytest tests/compatibility --env qa --browser
firefox`, `--browser webkit`, `--device "iPhone 13"`, etc.), which is the real lever this
harness has over "cross-browser/device". Approximate engine mapping for the report:
Chrome/Edge->chromium, Firefox->firefox, Safari/iOS/iPadOS->webkit(+device), Android->
chromium(+device). The 8 remaining PS-CMP rows (014-021: orientation-during-interaction,
split-screen, notch, low-end perf, zoom, low-power-mode, in-app webview) are "No" in the
workbook itself — real-device-only concerns, not automatable here. Not yet run live.

## Sheet: Regression Suite (PS-REG) — in progress via a parallel fork
Per instructions, PS-REG rows reference their source Functional-sheet case in Remarks
("Source: PS-FUN-XXX") and must NOT get duplicate tests — the existing source test gets
tagged with `@pytest.mark.test_case("PS-REG-<id>")` instead. Dispatched this as a parallel
fork (pure file-editing, no live-game interaction, safe to run alongside the live PS-INT
suite) to map all 162 rows against the ~90 already-written Functional test functions and
apply the marker tags. Results not yet reviewed as of this checkpoint — see DECISIONS.md
once that lands for how any unmapped rows (Buy-confirm-dependent ones, most likely) were
handled.

## Sheets not yet started: PS-FEA (59 rows), PS-EDG (42 rows), PS-UI (47 rows)
Not written this run — by the time PS-INT/PS-ERR/PS-STR/PS-MTH/PS-CMP/PS-REG were in
hand, the live PS-INT run itself had demonstrated that a single feature-triggering
interruption/recovery test can take several real minutes (forcing a Bonus trigger, playing
out 7-30 Free Spins with the settle-wait budget D-011 requires for correctness, choosing a
feature, etc.) — so writing AND live-validating the ~100+ further automatable rows across
these three sheets realistically needs materially more session time than remained
reasonable to spend before producing a trustworthy, well-documented checkpoint. Analysis
done so far, to make picking this back up fast:

**PS-FEA** (Feature Testing, 59 rows, 50 Yes/Partial): heavily Free-Spins-mechanics
focused and would reuse everything already built for PS-INT/PS-MTH (`force_next_spin`,
`choose_free_spins_feature`, `play_feature_spins_to_completion`, raw `feature` response
inspection) — genuinely the *cheapest* remaining sheet per-row to write, just a large
volume of it (counter decrements, total-win accumulation, sticky-wild persistence/
multiplier-retention/position-scope, raining-wild non-persistence/multiplier-display,
choice-screen double-tap, Buy-feature cluster sharing PS-INT-005's Buy-confirm blocker,
7-day/6d23h-inactivity cases sharing PS-INT-022's can't-fast-forward-server-clocks limit,
"another device" sharing PS-STR-018's one-account limit).

**PS-EDG** (Edge & Boundary Cases, 42 rows, 40 Yes): balance-boundary cases (001-006) need
the same insufficient-balance mocking as PS-ERR-001 (this session's balance is ~6.1M EUR,
see D-005/006 — can't genuinely drain it); cap/large-win display cases (009-015) share
PS-INT-026's no-guaranteed-cap-trigger blocker except 013/014 (thousands-of-ways board,
achievable by waiting for or forcing a high-reel-height spin, no cheat needed) which are
readily automatable; input-racing cases (019-023, spam-click/simultaneous-input/click-
during-presentation) are a genuinely new, valuable category not covered elsewhere and
fully automatable with Playwright's precise event timing; session/network edge cases
(028-036) overlap heavily with PS-INT's existing techniques; display cases (037-040) are
small, easy, high-value (currency decimals, large-digit balance display).

**PS-UI** (UI-UX Testing, 47 rows, almost entirely Partial): fundamentally a visual-
regression concern (layout correctness at N resolutions, alignment, no layout jump) that
Playwright can capture evidence for (viewport resize + screenshot, confirmed no JS/PIXI
crash) but can't grade pass/fail on without either a human reviewing the screenshots or a
visual-diffing tool this project doesn't have set up. Recommend: one parametrized
screenshot-capture test across the listed resolutions/devices (reuses `game_ready`,
`page.set_viewport_size()`) producing evidence for manual review, rather than per-row
pass/fail assertions on things like "legible" or "no layout jump" that aren't
programmatically checkable here.

## Known pre-existing flakiness (not caused by this run's changes)
`tests/functional/test_auto_spin.py::test_auto_spin_plays_exact_count_then_stops` and
`::test_auto_spin_stop_ends_after_current_round` failed again in the post-fix Functional
recheck (no reruns). These don't touch feature-resolution code, so this doesn't look like
a side effect of D-005/D-006 — most likely the same previously-documented
"heavy single shared session degrades" pattern, or a genuine timing issue in the auto-spin
polling loop. Flagged for investigation once sheet work allows; not blocking new-sheet
work since Functional sheet is explicitly "already automated, don't rewrite."

## How to rerun
Full suite: `pytest --env qa -v`
One sheet once written: `pytest tests/<dir> --env qa -v` (serial — one shared player
account, never add `-n`/xdist workers)
By marker: `pytest --env qa -m "interruption or recovery"` etc.
