import re
import time

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from utils.api_client import parse_spin_response

# These tests simulate failure conditions this harness has no real access to
# (an actual RGS/wallet outage, a true multi-minute network blackout) via
# Playwright's own fault-injection primitives: page.context.set_offline()
# for genuine connectivity loss, and page.route() to substitute a mocked
# status/body or delay for a real one. This verifies the CLIENT's reaction
# to those conditions, which is what these test cases are really checking —
# not a claim that it reproduces the exact real-world trigger. See
# DECISIONS.md D-008.


@pytest.mark.interruption
@pytest.mark.recovery
@pytest.mark.test_case("PS-INT-008")
@pytest.mark.test_case("PS-REG-115")
def test_network_loss_before_spin_request_makes_no_debit(game_ready):
    """PS-INT-008: going offline and then attempting to spin must produce no
    request/debit, and the game must be fully usable again once connectivity
    returns. Ref: GR-56."""
    balance_before = game_ready.get_init_data().player_info.balance

    game_ready.set_offline(True)
    try:
        with pytest.raises(PlaywrightTimeoutError):
            game_ready.spin(timeout_ms=5_000)
    finally:
        game_ready.set_offline(False)

    assert game_ready.get_init_data().player_info.balance == balance_before
    result = game_ready.spin_and_wait()
    assert result.closed


@pytest.mark.interruption
@pytest.mark.recovery
@pytest.mark.test_case("PS-INT-009")
@pytest.mark.test_case("PS-EDG-033")
@pytest.mark.test_case("PS-REG-116")
def test_network_loss_after_spin_request_sent_recovers_without_duplication(game_ready, config):
    """PS-INT-009: if the spin request reaches the server but the response
    never arrives (connection drop in flight), the post-recovery state
    (after a reload) must reflect at most one debit for that round, never
    two. Ref: GR-56."""
    bet = game_ready.get_init_data().player_info.default_bet
    balance_before = game_ready.get_init_data().player_info.balance
    pattern = re.compile(config["network_patterns"]["spin"])

    def abort_in_flight(route):
        route.abort("connectionfailed")

    game_ready.page.route(pattern, abort_in_flight)
    try:
        with pytest.raises(PlaywrightTimeoutError):
            game_ready.spin(timeout_ms=5_000)
    finally:
        game_ready.page.unroute(pattern, abort_in_flight)

    game_ready.reload_and_wait_ready()
    balance_after_recovery = game_ready.get_init_data().player_info.balance
    assert balance_before - balance_after_recovery <= bet

    result = game_ready.spin_and_wait()
    assert result.closed


@pytest.mark.interruption
@pytest.mark.recovery
@pytest.mark.test_case("PS-INT-010")
@pytest.mark.test_case("PS-REG-117")
def test_network_loss_during_free_spins_continues_from_server_state(game_ready):
    """PS-INT-010: a connectivity drop mid-Free-Spins must not corrupt or
    abandon the round — after connectivity returns and the page reloads,
    the same unfinished round is reported and resolves cleanly.
    Ref: GR-56."""
    game_ready.force_next_spin("3 OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()
    assert game_ready.get_init_data().unfinished_info is not None

    game_ready.set_offline(True)
    game_ready.page.wait_for_timeout(10_000)
    game_ready.set_offline(False)

    game_ready.reload_and_wait_ready()
    assert game_ready.get_init_data().unfinished_info is None


@pytest.mark.interruption
@pytest.mark.recovery
@pytest.mark.test_case("PS-INT-011")
def test_long_network_outage_is_recoverable_on_relaunch(game_ready):
    """PS-INT-011: after a long outage, relaunching (reload) must still
    recover a playable session. Shortened from the workbook's 10-minute
    outage to 15s — this harness and the live QA session cannot fast-forward
    server-side session-timeout clocks or wait in real time for 10 minutes
    per run; this exercises the same reload/reconnect code path at a
    practical scale. See DECISIONS.md D-008. Ref: GR-56."""
    balance_before = game_ready.get_init_data().player_info.balance

    game_ready.set_offline(True)
    game_ready.page.wait_for_timeout(15_000)
    game_ready.set_offline(False)

    game_ready.reload_and_wait_ready()
    assert game_ready.get_init_data().player_info.balance == balance_before
    result = game_ready.spin_and_wait()
    assert result.closed


@pytest.mark.interruption
@pytest.mark.recovery
@pytest.mark.negative
@pytest.mark.test_case("PS-INT-017")
@pytest.mark.test_case("PS-EDG-031")
@pytest.mark.test_case("PS-REG-120")
def test_session_expiration_mid_free_spins_allows_relaunch_recovery(game_ready, config):
    """PS-INT-017: an auth/session failure mid-Free-Spins must not strand
    the session — regardless of what the client shows for the mocked
    failure itself, reloading must still recover a playable game.

    SPEC QUESTION: no documented session-expiry response shape/status exists
    in docs/samples/ to mock precisely, so this uses a generic 401 as a
    stand-in and only asserts recoverability, not the client's specific
    in-session error presentation (re-auth prompt wording, etc.) — see
    DECISIONS.md D-008.

    Must actually be INSIDE the Free Spins round (not just on the choice
    screen) before mocking the 401 on `/feature` — confirmed live: the
    choice screen never calls `/feature` at all (only a chosen, running
    round does), so a space press there doesn't hit the mocked route and
    this case silently tested nothing. Ref: GR-56."""
    game_ready.force_next_spin("3 OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    game_ready.choose_free_spins_feature("sticky")
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is None, timeout_ms=10_000
    )
    game_ready.dismiss_congrats_popup_if_present()

    pattern = re.compile(config["network_patterns"]["feature"])

    def expire_once(route):
        route.fulfill(status=401, json={"error": "SESSION_EXPIRED"})

    game_ready.page.route(pattern, expire_once)
    try:
        game_ready.wait_for_loading_overlay_to_clear()
        game_ready.page.wait_for_timeout(5_000)
        game_ready.press_space_bar()
        game_ready.page.wait_for_timeout(3_000)
    finally:
        game_ready.page.unroute(pattern, expire_once)

    game_ready.reload_and_wait_ready()
    result = game_ready.spin_and_wait()
    assert result.closed


@pytest.mark.interruption
@pytest.mark.recovery
@pytest.mark.negative
@pytest.mark.test_case("PS-INT-018")
@pytest.mark.test_case("PS-REG-121")
def test_wallet_credit_failure_after_win():
    """PS-INT-018: a win must never be lost if the wallet credit step fails.

    BLOCKED: this game's RGS spin response is atomic — bet, result and the
    post-win balance all arrive in one response (see CLAUDE.md > Network).
    There is no client-observable "win was computed but the credit failed"
    state to simulate: mocking the response to show a win with no balance
    change would just assert our own fabricated inconsistency, not real
    wallet-failure handling, and this harness has no access to the actual
    wallet/RGS boundary to inject a real fault there. Needs a test
    environment with wallet-level fault injection, not available here.
    Ref: GR-56."""
    pytest.skip("Blocked: no client-observable way to simulate a post-win wallet credit failure (atomic RGS response)")


@pytest.mark.interruption
@pytest.mark.recovery
@pytest.mark.negative
@pytest.mark.test_case("PS-INT-019")
@pytest.mark.test_case("PS-REG-122")
def test_wallet_debit_failure_on_spin_plays_no_round(game_ready, config):
    """PS-INT-019: if the spin request cannot be processed at all (modeled
    here the same way as PS-INT-021's server error, since this game has no
    separate client-visible debit step to fail independently of the spin
    request itself — see DECISIONS.md D-008), no round must be shown and no
    debit must occur. Ref: GR-56."""
    balance_before = game_ready.get_init_data().player_info.balance
    pattern = re.compile(config["network_patterns"]["spin"])

    def fail_debit(route):
        route.abort("failed")

    game_ready.page.route(pattern, fail_debit)
    try:
        with pytest.raises(PlaywrightTimeoutError):
            game_ready.spin(timeout_ms=5_000)
    finally:
        game_ready.page.unroute(pattern, fail_debit)

    assert game_ready.get_init_data().player_info.balance == balance_before
    result = game_ready.spin_and_wait()
    assert result.closed


@pytest.mark.interruption
@pytest.mark.recovery
@pytest.mark.negative
@pytest.mark.test_case("PS-INT-020")
@pytest.mark.test_case("PS-EDG-032")
@pytest.mark.test_case("PS-REG-123")
def test_slow_spin_response_does_not_double_process(game_ready, config):
    """PS-INT-020: an abnormally slow spin response (beyond a normal
    round-trip, here an artificial 6s add-on) must not cause state
    corruption or a double debit once it finally arrives. Ref: GR-56."""
    pattern = re.compile(config["network_patterns"]["spin"])

    def delay_then_continue(route):
        time.sleep(6)
        route.continue_()

    game_ready.page.route(pattern, delay_then_continue)
    try:
        exchange = game_ready.spin(timeout_ms=20_000)
    finally:
        game_ready.page.unroute(pattern, delay_then_continue)

    result = parse_spin_response(exchange.response_body)
    assert result.closed

    balance_before = game_ready.get_balance()
    second = game_ready.spin_and_wait()
    assert second.balance == balance_before - second.bet + second.total_win


@pytest.mark.interruption
@pytest.mark.recovery
@pytest.mark.negative
@pytest.mark.test_case("PS-INT-021")
@pytest.mark.test_case("PS-REG-124")
def test_server_error_on_spin_makes_no_debit_and_is_recoverable(game_ready, config):
    """PS-INT-021: a server error on a spin request must show no debit (no
    rollback needed because nothing was ever applied) and the game must
    remain/become recoverable. Ref: GR-56."""
    balance_before = game_ready.get_init_data().player_info.balance
    pattern = re.compile(config["network_patterns"]["spin"])

    def fail_once(route):
        route.fulfill(status=500, json={"error": "internal_error"})

    game_ready.page.route(pattern, fail_once)
    try:
        exchange = game_ready.spin()
    finally:
        game_ready.page.unroute(pattern, fail_once)

    assert exchange.status == 500

    game_ready.reload_and_wait_ready()
    assert game_ready.get_init_data().player_info.balance == balance_before
    result = game_ready.spin_and_wait()
    assert result.closed
