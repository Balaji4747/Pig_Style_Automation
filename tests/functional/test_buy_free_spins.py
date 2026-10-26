from decimal import Decimal

import pytest

from utils.logger import get_logger

log = get_logger(__name__)


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
@pytest.mark.test_case("PS-REG-028")
def test_buy_feature_interface_shows_cost_and_controls(game_ready, init_data):
    """PS-FUN-057: Buy Feature opens showing cost (100x total bet) and both
    Confirm and Cancel."""
    panel = game_ready.open_buy_feature()
    bet = init_data.player_info.default_bet
    expected_cost = bet * init_data.player_info.bb_bet_multiplier_settings.get("FG1", 100)
    log.info("Bet: %s, expected cost: %s, panel cost: %s, panel stake: %s", bet, expected_cost, panel.cost_text(), panel.stake_text())
    assert Decimal(panel.cost_text().lstrip("€")) == expected_cost
    assert Decimal(panel.stake_text().lstrip("€")) == bet
    panel.cancel()


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-REG-029")
def test_buy_feature_cost_scales_with_bet(game_ready, init_data):
    """PS-FUN-058: Buy cost is exactly 100x the total bet at every bet
    level tested (min, default, max)."""
    multiplier = init_data.player_info.bb_bet_multiplier_settings.get("FG1", 100)
    for bet in (init_data.player_info.min_bet, init_data.player_info.default_bet, init_data.player_info.max_bet):
        bet_panel = game_ready.open_bet_panel()
        bet_panel.select_bet(f"{bet:.2f}")
        bet_panel.confirm()

        buy_panel = game_ready.open_buy_feature()
        log.info("Bet: %s, buy feature cost: %s", bet, buy_panel.cost_text())
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
    log.info("Balance before: %s, bet before: %s", balance_before, bet_before)

    panel = game_ready.open_buy_feature()
    panel.cancel()

    log.info("Balance after cancel: %s, bet after cancel: %s", game_ready.get_balance(), game_ready.get_displayed_bet_text())
    assert game_ready.get_balance() == balance_before
    assert game_ready.get_displayed_bet_text() == bet_before
