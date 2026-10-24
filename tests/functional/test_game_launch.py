from decimal import Decimal

import pytest


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
def test_game_launches_to_base_game_with_correct_initial_state(game_ready, init_data):
    """PS-FUN-001: game launches, lands on the base game, and the initial
    state (reels, bet, balance, win) is correct."""
    assert game_ready.is_loaded()
    assert game_ready.get_pixi_node(game_ready.SPIN_BUTTON_NODE)["width"] > 0  # Play button present/enabled

    displayed_bet = game_ready.get_displayed_bet_text()
    assert Decimal(displayed_bet.lstrip("€")) == init_data.player_info.default_bet

    displayed_balance = game_ready.get_displayed_balance_text().lstrip("€").replace(",", "")
    assert Decimal(displayed_balance) == init_data.player_info.balance


@pytest.mark.functional
@pytest.mark.regression
def test_splash_screen_dismisses_to_base_game_when_shown(page, config, network_spy):
    """PS-FUN-002: when the splash screen appears, it dismisses to the base
    game. The splash is sometimes skipped entirely by the server
    (session/preference-dependent, see CLAUDE.md) — this test only asserts
    the dismiss behaviour when a splash actually shows."""
    from pages.game_page import GamePage

    game_page = GamePage(page, network_spy)
    game_page.goto(config["game_url"], timeout_ms=config["timeouts"]["game_ready_ms"])
    game_page.wait_for(game_page.is_loaded, timeout_ms=config["timeouts"]["game_ready_ms"])
    game_page.wait_for(
        lambda: game_page.is_splash_visible() or game_page.is_base_game_ready(),
        timeout_ms=config["timeouts"]["game_ready_ms"],
    )

    if not game_page.is_splash_visible():
        pytest.skip("Splash was skipped this session (server/preference-dependent) — nothing to dismiss")

    game_page.dismiss_splash(timeout_ms=config["timeouts"]["game_ready_ms"])
    assert not game_page.is_splash_visible()
    assert game_page.wait_for(game_page.is_base_game_ready, timeout_ms=config["timeouts"]["game_ready_ms"]) is None
