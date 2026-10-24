# Decisions Log — Autonomous QA Automation Run

Started: 2026-10-24. Working autonomously per user instruction; no questions asked mid-run. Each entry: decision, reasoning, what I'd want reviewed.

## D-001: Workbook path differs from instructions
The task instructions reference `docs/test_cases/Pig_Style_QA_Test_Suite.xlsx`. The actual
file is `docs/Pig_Style_QA_Test_Suite (1).xlsx` (also visible at `Docs/...` — Windows
filesystem is case-insensitive, `docs` and `Docs` are the same directory). No
`docs/test_cases/` directory exists. Using the actual file as source of truth.
**Review**: confirm this is the right/latest workbook (not a newer version elsewhere).

## D-002: Repo had no git history
`Is a git repository: false` at task start — all prior session work (scaffold, page
objects, Functional sheet tests, CLAUDE.md) was uncommitted. Ran `git init` and made an
initial baseline commit of everything as-is before starting new work, so history from this
point forward is meaningful and PROGRESS.md/commits can show exactly where an interrupted
run stopped. **Review**: none needed, this is pure infrastructure.

## D-003: .gitignore adjusted to track defect text evidence, not binary evidence
`reports/` was fully gitignored. Added exceptions so `reports/EXECUTION_SUMMARY.md`,
`reports/Pig_Style_QA_Test_Suite_EXECUTED.xlsx`, and the text files inside
`reports/defects/<id>/` (bug_report.md, network.json, console.log,
expected_vs_actual.json) are tracked in git for review, while screenshots/video/trace
files stay local-only (large binaries, not meant for a git diff workflow). All evidence
files still get written to disk in full per the spec; only git tracking is narrowed.
**Review**: if you want everything (including binaries) in git, remove the `*.png`/
`*.webm`/`*.zip` deny lines I added.

## D-004: Stopped the in-flight full-suite rerun from the prior task
A background `pytest tests/functional/ --reruns 1` run from before this task was still
executing and showing a cluster of failures (test_auto_spin count/stop tests,
test_balance win-credit and displayed-balance tests, test_base_game reel-bounds test) that
did not clear even after one rerun each. This matches the previously-documented
"heavy single shared session degrades over a long run" pattern. Stopped it rather than
let it keep consuming the live session before I even start the new scope, so later sheets
don't inherit an already-degraded session. Investigating root cause is first on today's
list (see PROGRESS.md).

## D-005: Fixed a real bug in `GamePage.play_feature_spins_to_completion` (page object, not the Functional sheet itself)
Root cause of D-004's stuck session: a fresh `tests/test_smoke.py` run (brand-new context)
still failed on its first spin, with a failure screenshot showing the game mid "13 OUT OF
15 FREE SPINS" with a ~€6.1M balance. `play_feature_spins_to_completion()` pressed Space
immediately on each loop iteration with no settle delay, unlike `spin()` (which waits a
fixed 3s for the prior round's win-presentation animation to finish before pressing Space
— see CLAUDE.md's documented gotcha). A winning feature spin's Space-press was therefore
silently ignored while still celebrating, the subsequent `/feature` response never
arrived, `wait_for_response` timed out, and the loop treated that as "round complete" and
returned early — even with 2+ spins still outstanding. Every later `ensure_base_game_ready()`
call (which re-checks `unfinishedInfo` and calls `resolve_pending_feature()`) hit the exact
same early-exit, so the round could never actually drain across the whole session, letting
wins compound far past anything a real round would produce.
Fix: added the same `wait_for_loading_overlay_to_clear()` + 3s settle wait used by `spin()`
at the top of each `play_feature_spins_to_completion()` iteration, before pressing Space.
This is a page-object/fixture bug fix, not a Functional-sheet test rewrite — the Functional
sheet's own test files are untouched. It directly blocks every new sheet that touches
Free Spins (PS-FEA, PS-INT, PS-REG sources in test_free_spins.py), so fixing it now is a
prerequisite rather than scope creep.
**Review**: the existing `test_free_spins.py`/`test_buy_free_spins.py` Functional tests
should be rerun once the shared session is drained, to confirm this fix doesn't change
their outcome (it should only make them more reliable, not change assertions).

## D-006: Second fix needed — end-of-feature settle delay, not just mid-round
After D-005's fix, the stuck round progressed (13/15 -> 15/15) but `tests/test_smoke.py`
still failed, now on its own `spin_and_wait()` call with the game visibly still mid the
15th (final) free spin's reel-stop animation. Root cause: `is_base_game_ready()`
(`megawaysText` presence) reports ready even while the final free spin's win rollup is
still visually playing — the same "visible flag doesn't mean interactable" issue CLAUDE.md
already documents for the splash/spinBtn. `resolve_pending_feature()` was declaring the
feature resolved as soon as the response loop ended, with no account for that last
rollup+congrats sequence taking longer to settle than a mid-round spin's.
Fix: after the spin-completion loop, actively wait (10s) for the "Congratulations" popup
to appear before dismissing it (a real "this round has finished settling" signal, not a
guess), falling back to one blanket 5s wait if that feature variant shows no such popup.
**Confirmed fixed**: `tests/test_smoke.py` now passes end-to-end (fresh init -> spin ->
balance delta checked) after both fixes. Balance was left at a very large value
(~€6.1M+ EUR) by the earlier stuck loop across this whole multi-hour session — harmless
for a QA sandbox token, not touched/reset.
**Review**: both fixes are localized to `GamePage.play_feature_spins_to_completion` /
`resolve_pending_feature`; no Functional-sheet test files were edited.
