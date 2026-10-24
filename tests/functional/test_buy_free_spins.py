from decimal import Decimal

import pytest


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
def test_buy_feature_interface_shows_cost_and_controls(game_ready, init_data):
    """PS-FUN-057: Buy Feature opens showing cost (100x total bet) and both
    Confirm and Cancel."""
    panel = game_ready.open_buy_feature()
    bet = init_data.player_info.default_bet
    expected_cost = bet * init_data.player_info.bb_bet_multiplier_settings.get("FG1", 100)
    assert Decimal(panel.cost_text().lstrip("€")) == expected_cost
    assert Decimal(panel.stake_text().lstrip("€")) == bet
    panel.cancel()


@pytest.mark.functional
@pytest.mark.regression
def test_buy_feature_cost_scales_with_bet(game_ready, init_data):
    """PS-FUN-058: Buy cost is exactly 100x the total bet at every bet
    level tested (min, default, max)."""
    multiplier = init_data.player_info.bb_bet_multiplier_settings.get("FG1", 100)
    for bet in (init_data.player_info.min_bet, init_data.player_info.default_bet, init_data.player_info.max_bet):
        bet_panel = game_ready.open_bet_panel()
        bet_panel.select_bet(f"{bet:.2f}")
        bet_panel.confirm()

        buy_panel = game_ready.open_buy_feature()
        assert Decimal(buy_panel.cost_text().lstrip("€")) == bet * multiplier
        buy_panel.cancel()

    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()


@pytest.mark.functional
@pytest.mark.regression
def test_cancelling_buy_feature_makes_no_debit(game_ready):
    """PS-FUN-060: cancelling the Buy interface makes no debit and returns
    to the base game with the bet unchanged."""
    balance_before = game_ready.get_balance()
    bet_before = game_ready.get_displayed_bet_text()

    panel = game_ready.open_buy_feature()
    panel.cancel()

    assert game_ready.get_balance() == balance_before
    assert game_ready.get_displayed_bet_text() == bet_before
