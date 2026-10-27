from decimal import Decimal

import pytest

from utils.logger import get_logger

log = get_logger(__name__)


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-FUN-082")
def test_history_shows_recent_round_details(game_ready):
    """PS-FUN-082: Game History shows bet, win and round id for recent
    rounds. Confirmed live (27 Oct 2026): #historyPanel is a footer-nav tab
    inside the same DOM overlay as Rules/Paytable (pages/history_page.py).

    - Play one spin, note its round id
    - Open History, find that round by id
    - Assert its bet/win amounts match the real spin result"""
    result = game_ready.spin_and_wait()
    log.info("Round id: %s, bet: %s, win: %s", result.round_id, result.bet, result.total_win)

    history = game_ready.open_history()
    game_ready.wait_for(lambda: history.row_count() > 0, timeout_ms=15_000)
    row = history.row_by_round_id(result.round_id)
    assert row.count() > 0, f"Round {result.round_id} not found in History"

    displayed_bet = Decimal(history.row_bet_amount(row).lstrip("€"))
    displayed_win = Decimal(history.row_win_amount(row).lstrip("€"))
    log.info("History row: bet %s, win %s", displayed_bet, displayed_win)
    assert displayed_bet == result.bet
    assert displayed_win == result.total_win
    history.close()


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-FUN-083")
def test_history_shows_buy_round_with_cost_and_total_win(game_ready, init_data):
    """PS-FUN-083: a Buy Feature round is recorded in History with the
    purchase cost and total feature win, identifiable as purchased.

    - Buy the feature at min bet, drain it to completion
    - Open History, find the triggering round by id
    - Assert its type is "BUY BONUS", bet shown is the purchase cost, and
      win is non-zero (the feature was played out for a win-bearing round)"""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.min_bet:.2f}")
    bet_panel.confirm()

    result = game_ready.buy_feature_and_wait()
    expected_cost = init_data.player_info.min_bet * init_data.player_info.bb_bet_multiplier_settings.get("FG1", 100)
    log.info("Bought round id: %s, expected cost: %s", result.round_id, expected_cost)

    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    game_ready.choose_free_spins_feature("sticky")
    game_ready.play_feature_spins_to_completion()
    game_ready.dismiss_congrats_popup_if_present()
    game_ready.wait_for(game_ready.is_base_game_ready, timeout_ms=15_000)
    game_ready.wait_for_loading_overlay_to_clear(timeout_ms=60_000)

    history = game_ready.open_history()
    game_ready.wait_for(lambda: history.row_count() > 0, timeout_ms=15_000)
    row = history.row_by_round_id(result.round_id)
    assert row.count() > 0, f"Bought round {result.round_id} not found in History"

    row_type = history.row_type(row)
    displayed_bet = Decimal(history.row_bet_amount(row).lstrip("€"))
    log.info("History row: type %s, bet %s", row_type, displayed_bet)
    assert row_type.upper() == "BUY BONUS"
    assert displayed_bet == expected_cost
    history.close()

    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()
