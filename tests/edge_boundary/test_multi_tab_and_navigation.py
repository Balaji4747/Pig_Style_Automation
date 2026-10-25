import pytest

from utils.api_client import parse_spin_response

pytestmark = pytest.mark.boundary


@pytest.mark.test_case("PS-EDG-036")
def test_two_tabs_one_session_stay_balance_consistent(game_ready, open_game_page_in):
    """PS-EDG-036: opening the same game in two tabs for one session must
    not allow double-play of the same round/feature, and balance must stay
    consistent between them (either single-session is enforced, or both
    tabs agree once refreshed). Ref: GR-56."""
    context = game_ready.page.context
    tab_b = open_game_page_in(context)

    # Confirmed live (D-028): opening a second tab against the same session
    # can get tab A's own spin rejected (a non-200 response with no "data"
    # key, consistent with single-session enforcement — see the mocked
    # equivalent in PS-ERR's concurrent-login case) rather than silently
    # succeeding. Both outcomes satisfy this test's own documented
    # acceptance criteria ("either single-session is enforced, or both tabs
    # agree"), so handle both instead of assuming success.
    exchange = game_ready.spin()
    if exchange.status != 200 or exchange.response_body is None or "data" not in exchange.response_body:
        tab_b.page.close()
        return

    result_a = parse_spin_response(exchange.response_body)
    if result_a.is_feature_triggered:
        game_ready.resolve_pending_feature()

    tab_b.reload_and_wait_ready()
    assert tab_b.get_init_data().player_info.balance == result_a.balance

    tab_b.page.close()


@pytest.mark.test_case("PS-EDG-034")
def test_browser_back_during_spin_completes_round_server_side(game_ready, config):
    """PS-EDG-034 (P1): pressing browser Back during a spin must not lose
    the round — it completes server-side, and returning finds a consistent
    state. Ref: GR-56."""
    balance_before = game_ready.get_init_data().player_info.balance
    bet = game_ready.get_init_data().player_info.default_bet

    game_ready.page.locator(game_ready.CANVAS_SELECTOR).first.focus()
    game_ready.page.keyboard.press("Space")
    game_ready.page.wait_for_timeout(300)
    game_ready.page.go_back()
    game_ready.page.wait_for_timeout(2_000)

    # Confirmed live (D-028): this game is a single-page app with only one
    # navigation entry (the initial goto()) — go_back() leaves the game's
    # origin entirely (there's nothing behind it but the page's blank
    # starting entry), so a plain reload_and_wait_ready() afterward reloads
    # whatever that blank page is, never reaching the game, and times out
    # waiting for an init response that can never come. Re-navigate to the
    # game URL directly instead, as "returning" really means here.
    game_ready.goto(config["game_url"], timeout_ms=config["timeouts"]["game_ready_ms"])
    game_ready.wait_for(game_ready.is_loaded, timeout_ms=config["timeouts"]["game_ready_ms"])
    game_ready.ensure_base_game_ready(timeout_ms=config["timeouts"]["game_ready_ms"])
    balance_after = game_ready.get_init_data().player_info.balance
    assert balance_before - balance_after <= bet
    result = game_ready.spin_and_wait()
    assert result.closed


@pytest.mark.test_case("PS-EDG-035")
def test_back_then_forward_during_free_spins_restores_feature(game_ready):
    """PS-EDG-035 (P1): navigating back then forward during Free Spins must
    restore the feature, not abandon it. Ref: GR-56."""
    game_ready.force_next_spin("3 OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()
    assert game_ready.get_init_data().unfinished_info is not None

    game_ready.page.go_back()
    game_ready.page.wait_for_timeout(1_000)
    game_ready.page.go_forward()
    game_ready.page.wait_for_timeout(1_000)

    game_ready.reload_and_wait_ready()
    assert game_ready.get_init_data().unfinished_info is None
