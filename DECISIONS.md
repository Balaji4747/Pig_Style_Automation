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

## D-007: New pytest markers for the new sheets
Added `negative`, `boundary`, `integration` (the three "type" markers from the task's list
not already registered — `functional`/`math`/`recovery`/`ui`/`compatibility` already
existed), plus a `test_case(id)` marker so every test can declare the exact workbook
Test Case ID(s) it covers in a machine-queryable way (`pytest -m "test_case"` doesn't
filter by value, but `--collect-only -m ...` plus grep, or a small script, can map ID ->
test function — used for the final ID/function/status table and for confirming no PS-REG
row goes untagged). Error Handling (PS-ERR) tests use `negative`; STR/Transaction tests use
`integration` (no dedicated "transaction" marker — the task's own marker list didn't
include one, and `integration` reads correctly for cross-request transaction checks).
**Review**: if you'd prefer a dedicated `transaction` marker instead of reusing
`integration` for PS-STR, easy to rename.

## D-008: PS-INT feasibility — what "Yes" actually means here
All 30 PS-INT rows are marked Automation Candidate "Yes" in the workbook, but several
describe conditions Playwright cannot literally produce (real iOS/Android app
backgrounding, an incoming phone call, a locked device, an actual wallet-service outage,
a real 24-hour or 10-minute elapsed-time gap, a genuine browser process crash). Rather than
skip these or silently fake full compliance, each gets the closest *real* automated
equivalent, named explicitly in its docstring, and is scored against what it actually
proves:
- **Network loss / server errors / timeouts / session expiry** (PS-INT-008/009/010/011/
  017/018/019/020/021): `page.context.set_offline(True)` for true connectivity loss, and
  `page.route()` response mocking (abort, delay, or a substituted status/body) for
  server-side failure modes we have no real fault-injection access to. This is standard
  practice for testing a client's failure handling and is treated as full "Yes" automation
  of the *client-side reaction*, not a claim that it reproduces the real RGS/wallet failing.
- **Refresh / close-reopen / browser crash / reload-based cases** (001-007, 022-026,
  028-030): `page.reload()` or closing and reopening a page/context against the same
  session token — genuinely exercises the real recovery path (`unfinishedInfo`,
  `resolve_pending_feature`), scored "Yes".
- **Device rotation** (016): `page.set_viewport_size()` mid-presentation — this is a real,
  supported Playwright capability and a faithful equivalent, scored "Yes".
- **App background (iOS/Android), device lock, incoming call** (012-015): approximated via
  dispatching a `visibilitychange`/`document.hidden` event, which is the standard web-layer
  signal a page receives in all of these real scenarios. This tests the game's reaction to
  *that signal*, not the native OS behavior around it (and can't touch audio restoration at
  all) — scored "Partial", with the gap stated in each docstring.
- **Long elapsed-time gaps** (10 min outage in 011, 24h unfinished-round in 022):
  shortened to a practical duration (tens of seconds) that still exercises the same
  reload/reconnect code path, since neither this harness nor the live session can fast-
  forward server-side clocks or wait in real-time for hours. Scored "Partial", gap stated.
- **Max win cap** (026): depends on hitting the live max-win cap deterministically. The
  cheat tool's win-tier options ("BIG WIN"/"MEGA WIN"/"GIGA WIN"/"UNBEL WIN") share mostly
  identical forced boards and may not reach the cap at every bet level — tried at max bet
  first; if `maxCapReached` never comes back true, this is marked Blocked ("needs cheat for
  guaranteed max-win-cap trigger") rather than faked.
**Review**: if a stricter reading of "Yes" is wanted (i.e., only count a case as automated
when it reproduces the literal real-world trigger), most of 008-021 and all of 012-015
should be downgraded to Partial/Blocked instead — flagging this explicitly since it's a
judgment call with a real difference in what the resulting test actually proves.

## D-009: Functional-suite recheck's cascading failures were self-inflicted (two concurrent runs on one shared account)
While trying to launch the Functional-suite recheck in the background, my first attempt
used `run_in_background: true` on a Bash call that ALSO backgrounded the pytest command
itself internally with a trailing `&`. The outer wrapper exited immediately (having done
nothing but launch pytest and echo its PID) and reported "completed", which I mistakenly
read as the pytest run finishing. In fact the detached pytest process kept running,
untracked, in the background. I then launched a second, properly-tracked recheck run on
top of it — meaning **two pytest processes were hitting the one shared QA player session
concurrently** for a stretch of this run, which is exactly the "never run anything but
serially against the one account" rule this whole task is built on. That fully explains
the cascading `test_auto_spin`/`test_balance` failures (including
`test_balance_debited_by_exactly_the_bet_amount`, which had passed cleanly in every prior
run) — concurrent spins and reads against one account race on balance and round state.
Found via `ps aux` showing a second, older `python` process still alive after the tracked
task was stopped; killed it (`kill -9`), confirmed no python/chromium processes remain.
**This is a test-infrastructure bug on my end, not a product defect** — none of the
Functional-suite failures from this recheck should be trusted or reported as bugs. Redoing
the recheck now as a single, properly-tracked run before drawing any conclusion about
whether D-005/D-006 broke anything.
**Review**: no code changes needed; this is a process-hygiene note for future background
launches — never combine `run_in_background: true` with an internal `&`/detached child.
