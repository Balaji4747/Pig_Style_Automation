from decimal import Decimal

import pytest

pytestmark = [pytest.mark.functional, pytest.mark.regression, pytest.mark.recovery]


@pytest.mark.test_case("PS-FEA-054")
@pytest.mark.test_case("PS-REG-094")
def test_close_browser_mid_fs_and_relaunch_restores_feature(game_ready, open_game_page_in, trigger_and_choose):
    """PS-FEA-054: closing the browser mid-Free-Spins and relaunching must
    restore the feature. Ref: GR-56."""
    trigger_and_choose(3, "sticky")
    context = game_ready.page.context
    game_ready.page.close()

    relaunched = open_game_page_in(context)
    assert relaunched.get_init_data().unfinished_info is None, "feature should have resolved on relaunch"
    result = relaunched.spin_and_wait()
    assert result.closed


@pytest.mark.test_case("PS-FEA-055")
def test_unfinished_feature_resumes_on_another_device():
    """PS-FEA-055 (P1, Partial): an unfinished feature must resume for the
    same player on a different device. BLOCKED: this environment provides
    exactly one player token/session — "another device" would need a
    second distinct login for the same player account, which the one-
    account constraint this whole suite runs under doesn't provide. The
    SAME-session equivalent (reload/relaunch resuming correctly) is already
    covered extensively elsewhere (PS-INT-003/022-025, PS-FEA-010/022/054).
    Ref: GR-56."""
    pytest.skip("Blocked: only one player session is available in this environment")


@pytest.mark.test_case("PS-FEA-056")
@pytest.mark.test_case("PS-REG-095")
def test_unfinished_feature_after_7_days_inactivity():
    """PS-FEA-056 (P0): behaviour after 7+ days of inactivity. Not
    automated — the workbook marks this "No" itself, and for good reason:
    the expected behaviour is an open SPEC QUESTION (OBS-23 — "may be
    forfeited" conflicts with jurisdictions that require preserving player
    winnings) with no confirmed answer to assert against, and this harness
    cannot fast-forward the server's own real-time clock by 7 days anyway.
    Ref: GR-58 | OBS-23."""
    pytest.skip("Not automated: workbook marks this No — undefined expected behavior (OBS-23) and no time-shift capability")


@pytest.mark.test_case("PS-FEA-057")
def test_unfinished_feature_restored_before_7_days():
    """PS-FEA-057 (P1): a feature left unfinished for 6 days 23 hours must
    still be restored intact. Not automated — the workbook marks this "No"
    itself; this harness has no way to fast-forward the server's real-time
    inactivity clock by nearly 7 days. The near-immediate equivalent (an
    unfinished round reload a few seconds/minutes later) is already covered
    by PS-FEA-010/022 and the whole PS-INT reload suite. Ref: GR-58."""
    pytest.skip("Not automated: workbook marks this No — no time-shift capability in this environment")


@pytest.mark.test_case("PS-FEA-058")
@pytest.mark.test_case("PS-REG-096")
def test_network_drop_during_fs_spin_request_recovers_without_spin_loss(game_ready, trigger_and_choose):
    """PS-FEA-058: a network drop during an FS spin request must be
    recovered without losing that spin (reconnect, result displayed once,
    counter correct) — verified via no-duplicate-round-id after recovery,
    the same invariant used throughout PS-INT's network-fault cases.
    Ref: GR-56."""
    trigger_and_choose(3, "sticky")
    game_ready.network_spy.clear("feature")

    game_ready.set_offline(True)
    game_ready.wait_for_loading_overlay_to_clear()
    game_ready.page.wait_for_timeout(3_000)
    game_ready.press_space_bar()
    game_ready.page.wait_for_timeout(3_000)
    game_ready.set_offline(False)

    game_ready.reload_and_wait_ready()
    round_ids = [e.response_body["data"]["roundId"] for e in game_ready.network_spy.all("feature")]
    assert len(round_ids) == len(set(round_ids)), "a feature spin was processed more than once after a network drop"


@pytest.mark.test_case("PS-FEA-059")
@pytest.mark.test_case("PS-REG-097")
def test_refresh_on_fs_summary_screen_does_not_credit_twice(game_ready, trigger_and_choose, play_one_feature_spin):
    """PS-FEA-059: refreshing on the Free Spins summary screen must not
    credit the total twice. Plays the round to completion (so the summary
    is genuinely showing), captures the balance, then reloads and confirms
    it is unchanged. Ref: GR-12, GR-56."""
    trigger_and_choose(3, "sticky")
    for _ in range(10):
        if play_one_feature_spin() is None:
            break

    # The round should be fully drained by now (play_one_feature_spin loops
    # until no more /feature responses arrive) — at the natural summary
    # point, reload and confirm balance doesn't move.
    balance_at_summary = game_ready.get_balance()
    game_ready.reload_and_wait_ready()
    assert game_ready.get_init_data().player_info.balance == balance_at_summary
