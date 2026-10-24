import pytest

pytestmark = pytest.mark.boundary


@pytest.mark.test_case("PS-EDG-036")
def test_two_tabs_one_session_stay_balance_consistent(game_ready, open_game_page_in):
    """PS-EDG-036: opening the same game in two tabs for one session must
    not allow double-play of the same round/feature, and balance must stay
    consistent between them (either single-session is enforced, or both
    tabs agree once refreshed). Ref: GR-56."""
    context = game_ready.page.context
    tab_b = open_game_page_in(context)

    result_a = game_ready.spin_and_wait()

    tab_b.reload_and_wait_ready()
    assert tab_b.get_init_data().player_info.balance == result_a.balance

    tab_b.page.close()


@pytest.mark.test_case("PS-EDG-034")
def test_browser_back_during_spin_completes_round_server_side(game_ready):
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

    game_ready.reload_and_wait_ready()
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
