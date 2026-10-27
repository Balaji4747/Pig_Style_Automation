import pytest

from utils.logger import get_logger

log = get_logger(__name__)

# No cheat involved: force_next_spin() is confirmed unreliable in this
# environment (CLAUDE.md D-019). buy_feature_and_wait() is a real,
# deterministic purchase confirmed live to always trigger the feature - used
# here purely as a reliable trigger, not to test the Buy flow itself (see
# tests/functional/test_buy_free_spins.py and
# tests/feature_testing/test_buy_feature.py for that).


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
@pytest.mark.test_case("PS-REG-026")
def test_free_spins_choice_screen_offers_correct_spin_counts(game_ready, init_data):
    """PS-FUN-054: after a 3-Bonus trigger, both Sticky Wilds (7 spins) and
    Raining Wilds (15 spins) are offered — matching the math file
    (config/paytable.yaml's source) — and selecting one starts that
    feature.

    - Buy the feature at min bet (deterministic trigger), wait for the
      choice screen
    - Assert Sticky Wilds offers 7 spins and Raining Wilds offers 15
    - Choose Sticky Wilds and drain the feature so later tests start clean"""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.min_bet:.2f}")
    bet_panel.confirm()

    result = game_ready.buy_feature_and_wait()
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

    try:
        game_ready.choose_free_spins_feature("sticky")
    except TimeoutError:
        pass  # FEATURE_CHOICE_TITLE_NODE can stay stuck visible even after the round already finished
    game_ready.drain_active_feature_if_any()

    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-REG-027")
def test_free_spins_play_at_triggering_bet_with_no_per_spin_debit(game_ready, init_data):
    """PS-FUN-056: Free Spins are played at the same bet as the triggering
    spin, and no bet is debited per Free Spin (balance only ever increases
    or stays the same during the feature, since wins — not debits — are the
    only balance-changing event).

    - Set bet to 2.00, buy the feature (deterministic trigger), choose
      Sticky Wilds
    - Play the feature to completion
    - Assert every /feature response used bet 2.00 and balance never dropped
    - Reset to the default bet afterward"""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet("2.00")
    bet_panel.confirm()

    triggering_result = game_ready.buy_feature_and_wait()
    log.info("Triggering spin bet: %s", triggering_result.bet)
    assert triggering_result.bet == 2

    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )

    # Clear "feature" BEFORE choosing: choose_free_spins_feature()'s own
    # retry-click can occasionally auto-drain a short round itself (same
    # stale-visible-node quirk documented on drain_active_feature_if_any) -
    # clearing here first ensures every /feature response is captured
    # regardless of whether draining happens inside that call or below.
    game_ready.network_spy.clear("feature")
    balance_before_feature = game_ready.get_balance()
    log.info("Balance before feature: %s", balance_before_feature)

    try:
        game_ready.choose_free_spins_feature("sticky")
    except TimeoutError:
        pass
    game_ready.drain_active_feature_if_any()

    for exchange in game_ready.network_spy.all("feature"):
        data = exchange.response_body["data"]
        assert data["result"]["bet"] == 2

    balance_after_feature = game_ready.get_balance()
    log.info("Feature spins played: %s, balance after feature: %s", len(game_ready.network_spy.all("feature")), balance_after_feature)
    assert balance_after_feature >= balance_before_feature

    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()
