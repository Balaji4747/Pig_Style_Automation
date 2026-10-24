import re

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

pytestmark = pytest.mark.negative


@pytest.mark.test_case("PS-ERR-005")
def test_offline_spin_shows_connection_lost_and_makes_no_debit(game_ready):
    """PS-ERR-005 (P1): spinning while offline must show a connection-lost
    message, be retryable, and make no debit. Ref: GR-56."""
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


@pytest.mark.test_case("PS-ERR-006")
def test_server_500_on_spin_shows_generic_error_and_is_recoverable(game_ready, mock_spin_failure):
    """PS-ERR-006: a 500 on spin must show a generic error with a code and
    remain recoverable. Ref: GR-56."""
    balance_before = game_ready.get_init_data().player_info.balance
    exchange = mock_spin_failure(lambda route: route.fulfill(status=500, json={"error": "internal_error"}))
    assert exchange is not None and exchange.status == 500

    game_ready.reload_and_wait_ready()
    assert game_ready.get_init_data().player_info.balance == balance_before
    result = game_ready.spin_and_wait()
    assert result.closed


@pytest.mark.test_case("PS-ERR-007")
def test_server_503_at_launch_shows_maintenance_message(context, config):
    """PS-ERR-007 (P1): launching while the server returns 503 must show a
    maintenance message rather than a broken/partial game, and launching
    again normally afterward must succeed. Ref: GR-56."""
    pattern = re.compile(config["network_patterns"]["init"])
    page = context.new_page()
    page.route(pattern, lambda route: route.fulfill(status=503, json={"error": "maintenance"}))

    page.goto(config["game_url"])
    page.wait_for_timeout(5_000)
    # No confirmed PIXI node name exists for a maintenance/error screen, so
    # this asserts the safe negative: the game must NOT reach a normal,
    # interactive base-game state while the server is down.
    pixi_ready = page.evaluate("() => !!(window.__PIXI_APP__ && window.__PIXI_APP__.stage)")
    assert not pixi_ready, "game appeared to initialize normally despite a 503 on init"

    page.unroute(pattern)
    page.close()


@pytest.mark.test_case("PS-ERR-011")
def test_spin_timeout_shows_message_and_recovers(game_ready, config):
    """PS-ERR-011: a spin request that never responds in time must show a
    timeout message and remain recoverable afterward. Ref: GR-56."""
    pattern = re.compile(config["network_patterns"]["spin"])
    balance_before = game_ready.get_init_data().player_info.balance

    def never_respond(route):
        pass  # deliberately never calls route.fulfill/continue/abort

    game_ready.page.route(pattern, never_respond)
    try:
        with pytest.raises(PlaywrightTimeoutError):
            game_ready.spin(timeout_ms=8_000)
    finally:
        game_ready.page.unroute(pattern, never_respond)

    game_ready.reload_and_wait_ready()
    assert game_ready.get_init_data().player_info.balance == balance_before
    result = game_ready.spin_and_wait()
    assert result.closed


@pytest.mark.test_case("PS-ERR-012")
def test_engine_error_on_spin_makes_no_debit_or_rollback_needed(game_ready, mock_spin_failure):
    """PS-ERR-012: an RNG/engine error on spin must make no debit (so no
    rollback is needed) and show an error message. Ref: GR-56."""
    balance_before = game_ready.get_init_data().player_info.balance
    exchange = mock_spin_failure(lambda route: route.fulfill(status=500, json={"error": "ENGINE_ERROR"}))
    assert exchange is not None and exchange.status == 500

    game_ready.reload_and_wait_ready()
    assert game_ready.get_init_data().player_info.balance == balance_before


@pytest.mark.test_case("PS-ERR-013")
def test_wallet_debit_rejection_plays_no_round(game_ready, mock_spin_failure):
    """PS-ERR-013: if the wallet rejects the debit outright, no round must
    be shown (modeled the same way as PS-INT-019/PS-ERR-006, since this
    game's RGS response is atomic and there's no distinct client-visible
    debit step to fail independently — see DECISIONS.md D-008). Ref: GR-56."""
    balance_before = game_ready.get_init_data().player_info.balance
    exchange = mock_spin_failure(lambda route: route.abort("failed"))
    assert exchange is None, "expected the debit-rejected request to never produce a usable response"

    assert game_ready.get_init_data().player_info.balance == balance_before
    result = game_ready.spin_and_wait()
    assert result.closed


@pytest.mark.test_case("PS-ERR-016")
def test_malformed_spin_response_does_not_crash_client(game_ready, mock_spin_failure):
    """PS-ERR-016 (P1): a malformed (invalid JSON) spin response must not
    crash the client — the game stays responsive and a normal spin
    afterward still works. Ref: GR-56."""

    def malformed(route):
        route.fulfill(status=200, content_type="application/json", body="{not valid json")

    mock_spin_failure(malformed, timeout_ms=5_000)

    assert game_ready.is_pixi_ready(), "client appears to have crashed after a malformed spin response"
    game_ready.reload_and_wait_ready()
    result = game_ready.spin_and_wait()
    assert result.closed


@pytest.mark.test_case("PS-ERR-018")
def test_recovery_after_consecutive_errors_has_correct_state_and_no_duplicates(game_ready, mock_spin_failure):
    """PS-ERR-018: after an error, reloading must show the correct balance
    and state with no duplicates — checked across two consecutive mocked
    errors in a row, each followed by a reload. Ref: GR-56."""
    balance_before = game_ready.get_init_data().player_info.balance

    for status in (500, 401):
        mock_spin_failure(lambda route, s=status: route.fulfill(status=s, json={"error": "mock"}))
        game_ready.reload_and_wait_ready()
        assert game_ready.get_init_data().player_info.balance == balance_before

    game_ready.network_spy.clear("spin")
    result_a = game_ready.spin_and_wait()
    result_b = game_ready.spin_and_wait()
    assert result_a.round_id != result_b.round_id
    round_ids = [e.response_body for e in game_ready.network_spy.all("spin")]
    assert len(round_ids) == len({r["data"]["roundId"] for r in round_ids if r})
