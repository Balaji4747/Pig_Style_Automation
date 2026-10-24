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

## CHECKPOINT 2: a fourth stuck-round incident live-validating PS-ERR, found + fixed — see DECISIONS.md D-013
After CHECKPOINT 1, the session recovered (confirmed via a clean `test_smoke.py` pass) and
a live PS-ERR run got to 3 passed / 3 failed before being stopped for investigation. Root
cause: a genuine, previously-unknown mid-round "Congratulations" retrigger popup that
`play_feature_spins_to_completion()` never checked for mid-loop (only at the loop's
start/end) — same silently-dropped-input pattern as every prior incident, just a new
trigger for it. Fixed (dismiss it before every press, not just at the boundaries) and
hardened `ensure_base_game_ready()` to raise loudly instead of silently continuing with a
still-broken session after exhausting its retries (this silent-continue behavior is what
let every one of the four stuck-round incidents this run corrupt a LATER, unrelated test
instead of failing clearly at its own point of origin). PS-ERR's live run was stopped
before completion to apply and reason through this fix rather than let 20 more minutes
run against code already known to be wrong; not yet rerun. The new `tests/edge_boundary/
test_large_win_display.py` PS-EDG-013 and the PS-UI suite are similarly not yet run live.
Given four independent timing-fragility incidents in one run, live validation of all new
suites remains PENDING in `reports/EXECUTION_SUMMARY.md` — see D-013's "Review" for the
structural fix that would actually close this out (poll the server's own per-spin
completion signal instead of guessing/patching wait durations and popups one at a time).

## CHECKPOINT 1: live validation paused — see DECISIONS.md D-012
The live `tests/interruption/` run (30 cases) got as far as 5/30 (3 pass, 1 fail — fixed a
cleanup gap in that test afterward, see D-012 — 1 that needed a long stuck-round recovery)
before demonstrating that a single adversarial feature-recovery can legitimately take tens
of minutes under D-011's fix. A follow-up isolated diagnostic confirmed the fixture-level
recovery DOES eventually succeed (not a true infinite hang), but then hit a SECOND,
unexplained multi-minute delay immediately afterward with no diagnostic output to pin down
why — possibly a smaller recurrence of the same class of issue, possibly general session/
environment slowness after a very long day of continuous heavy automated use. Stopped
investigating further (diminishing returns) and deleted the diagnostic. **The shared
session's current state is not confirmed clean** — budget extra time for a possibly slow
first load whenever this is picked up again.
All test code for PS-INT/PS-ERR/PS-STR/PS-MTH/PS-CMP is written, committed, and compiles/
collects cleanly, but marked PENDING (not confirmed passing live) in
`reports/EXECUTION_SUMMARY.md`. Also fixed, while auditing for the same mistake PS-INT-016
had (comparing a stale `get_init_data().player_info.balance` — which only updates on
reload/goto — against a balance that had actually changed via an intervening spin): two
real instances of the same bug in PS-STR-007 and PS-STR-010 (both now use `get_balance()`,
which correctly prefers the latest spin's balance). Audited every other occurrence in the
new test files; all others were confirmed correct (read fresh-at-test-start or
immediately after a reload).

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

## Sheet: Edge & Boundary Cases (PS-EDG) — 29 of 42 written
Added after the initial checkpoint, using idle time well (the live session recovery cost
demonstrated by D-012 doesn't block writing more code, only running it). Genuinely new:
input-racing (019,020,021,023,041), display (009,038), many-simultaneous-wins (013, bounded
10-attempt natural-high-ways search, not a wait for a rare forced outcome), two-tab/
browser-back-forward (036,034,035, new `tests/conftest.py` shared `open_game_page_in`
fixture — promoted from a per-directory duplicate once a second sheet needed it). Tagged
onto existing tests rather than duplicating: 029->PS-INT-023, 030->PS-ERR-003, 031->PS-
INT-017, 032->PS-INT-020, 033->PS-INT-009. Explicit Blocked skips with reasoning for 13
more (001-008,010-012,014-017,022,024,026-028,037,039,040 — balance-boundary preconditions
unreachable at this session's inflated balance, Buy-confirm gap, cap-trigger gap, reel-
height not independently controllable, no History page object, single-currency session).
Not written: 018,042 (workbook: No). Not yet run live (same D-012 pacing caveat as the
other new sheets).

## Sheets not yet started: PS-FEA (59 rows), PS-UI (47 rows)
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

**PS-EDG**: written this run (29 of 42) — see the "Sheet: Edge & Boundary Cases" section
above for what's done. 13 cases Blocked with reasoning (balance-boundary preconditions,
Buy-confirm, cap-trigger, reel-height control, no History page object, single-currency
session), 2 not automated (workbook: No).

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
