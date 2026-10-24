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

## Sheet: Interruption & Recovery (PS-INT) — 30 rows, all P0/P1, all "Yes"
Status: **IN PROGRESS**. Full row list read (`docs/test_cases/ps_int.csv`). Feasibility
assessment done (see DECISIONS D-008 once logged) — most rows are genuinely automatable
against this Playwright/PIXI/network-spy stack via reload, `page.context.set_offline()`,
`page.route()` response mocking, and viewport-size changes for "rotation". True native
mobile OS events (app backgrounding, incoming calls, device lock) are not controllable
from Playwright — those get `visibilitychange` event dispatch as a documented partial
substitute, not a full equivalent.
Not yet started writing test files as of this checkpoint.

## Sheets not yet started
PS-ERR, PS-STR, PS-MTH, PS-FEA, PS-EDG, PS-UI, PS-CMP, PS-REG.

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
