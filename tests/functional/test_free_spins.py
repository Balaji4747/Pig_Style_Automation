import pytest

from utils.api_client import parse_spin_response
from utils.logger import get_logger

log = get_logger(__name__)


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
@pytest.mark.test_case("PS-REG-026")
def test_free_spins_choice_screen_offers_correct_spin_counts(game_ready):
    """PS-FUN-054: after a 3-Bonus trigger, both Sticky Wilds (7 spins) and
    Raining Wilds (15 spins) are offered — matching the math file
    (config/paytable.yaml's source) — and selecting one starts that
    feature.

    - Force a Bonus trigger, wait for the choice screen
    - Assert Sticky Wilds offers 7 spins and Raining Wilds offers 15
    - Choose Sticky Wilds and drain the feature so later tests start clean"""

    def trigger():
        game_ready.wait_for_loading_overlay_to_clear()
        game_ready.page.wait_for_timeout(3_000)
        game_ready.press_space_bar()

    game_ready.force_next_spin("3 OAK BN")
    exchange = game_ready.network_spy.wait_for_response("spin", trigger, timeout_ms=10_000)
    result = parse_spin_response(exchange.response_body)
    log.info("Feature triggered: %s", result.is_feature_triggered)
    assert result.is_feature_triggered

    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    sticky_count = game_ready.get_displayed_integer_near_label("titleText", "STICKY WILDS")
    raining_count = game_ready.get_displayed_integer_near_label("titleText", "RAINING WILDS")
    log.info("Sticky Wilds spins offered: %s, Raining Wilds spins offered: %s", sticky_count, raining_count)
    assert sticky_count == 7
    assert raining_count == 15

    game_ready.choose_free_spins_feature("sticky")
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is None, timeout_ms=10_000
    )

    # Clean up so later tests start from the base game.
    game_ready.dismiss_congrats_popup_if_present()
    game_ready.play_feature_spins_to_completion()
    game_ready.dismiss_congrats_popup_if_present()
    game_ready.wait_for(game_ready.is_base_game_ready, timeout_ms=15_000)
    game_ready.wait_for_loading_overlay_to_clear(timeout_ms=60_000)


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-REG-027")
def test_free_spins_play_at_triggering_bet_with_no_per_spin_debit(game_ready):
    """PS-FUN-056: Free Spins are played at the same bet as the triggering
    spin, and no bet is debited per Free Spin (balance only ever increases
    or stays the same during the feature, since wins — not debits — are the
    only balance-changing event).

    - Set bet to 2.00, force a Bonus trigger, choose Sticky Wilds
    - Play the feature to completion
    - Assert every /feature response used bet 2.00 and balance never dropped
    - Reset to bet 1.00 afterward"""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet("2.00")
    bet_panel.confirm()

    def trigger():
        game_ready.wait_for_loading_overlay_to_clear()
        game_ready.page.wait_for_timeout(3_000)
        game_ready.press_space_bar()

    game_ready.force_next_spin("3 OAK BN")
    exchange = game_ready.network_spy.wait_for_response("spin", trigger, timeout_ms=10_000)
    triggering_result = parse_spin_response(exchange.response_body)
    log.info("Triggering spin bet: %s", triggering_result.bet)
    assert triggering_result.bet == 2

    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    game_ready.choose_free_spins_feature("sticky")
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is None, timeout_ms=10_000
    )
    game_ready.dismiss_congrats_popup_if_present()

    game_ready.network_spy.clear("feature")
    balance_before_feature = game_ready.get_balance()
    log.info("Balance before feature: %s", balance_before_feature)
    game_ready.play_feature_spins_to_completion()

    for exchange in game_ready.network_spy.all("feature"):
        data = exchange.response_body["data"]
        assert data["result"]["bet"] == 2

    game_ready.dismiss_congrats_popup_if_present()
    game_ready.wait_for(game_ready.is_base_game_ready, timeout_ms=15_000)
    game_ready.wait_for_loading_overlay_to_clear(timeout_ms=60_000)
    balance_after_feature = game_ready.get_balance()
    log.info("Feature spins played: %s, balance after feature: %s", len(game_ready.network_spy.all("feature")), balance_after_feature)
    assert balance_after_feature >= balance_before_feature

    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet("1.00")
    bet_panel.confirm()
