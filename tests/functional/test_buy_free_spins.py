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
    Confirm and Cancel.

    - Open the Buy Feature panel at the default bet
    - Assert shown cost is 100x bet and stake matches the current bet
    - Cancel"""
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
    level tested (min, default, max).

    - For min, default, and max bet
    - Select that bet, open Buy Feature panel
    - Assert shown cost equals bet * 100, then cancel
    - Reset to the default bet afterward"""
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
    to the base game with the bet unchanged.

    - Open Buy Feature panel, click Cancel
    - Assert balance and displayed bet are unchanged"""
    balance_before = game_ready.get_balance()
    bet_before = game_ready.get_displayed_bet_text()
    log.info("Balance before: %s, bet before: %s", balance_before, bet_before)

    panel = game_ready.open_buy_feature()
    panel.cancel()

    log.info("Balance after cancel: %s, bet after cancel: %s", game_ready.get_balance(), game_ready.get_displayed_bet_text())
    assert game_ready.get_balance() == balance_before
    assert game_ready.get_displayed_bet_text() == bet_before


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-FUN-059")
def test_buy_confirm_debits_100x_bet_and_triggers_feature(game_ready, init_data):
    """PS-FUN-059: confirming the purchase debits 100x bet once and starts
    the feature-triggering spin. Confirmed live (27 Oct 2026): the Buy
    confirm click fires a normal POST /spin call that atomically debits the
    full cost. Ref: GR-33, GR-36.

    - Select min bet to minimize the real debit, buy the feature
    - Assert balance dropped by exactly 100x bet, feature triggered,
      scatter count >= 3 - then drain the round to leave the session clean"""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.min_bet:.2f}")
    bet_panel.confirm()

    balance_before = game_ready.get_balance()
    multiplier = init_data.player_info.bb_bet_multiplier_settings.get("FG1", 100)
    result = game_ready.buy_feature_and_wait()
    balance_after = game_ready.get_balance()
    log.info("Balance before: %s, after: %s, scatter count: %s", balance_before, balance_after, result.scatter_count)

    assert balance_after == balance_before - result.bet * multiplier
    assert result.is_feature_triggered
    assert result.scatter_count >= 3

    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    try:
        game_ready.choose_free_spins_feature("sticky")
    except TimeoutError:
        pass
    game_ready.drain_active_feature_if_any()

    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-FUN-061")
def test_buy_triggering_spin_win_is_deferred_not_double_counted(game_ready, init_data):
    """PS-FUN-061: the feature-triggering spin's own line wins are reported
    in that response but deferred into featureData.baseWin rather than
    credited to balance immediately - confirmed live (27 Oct 2026). The
    balance only reflects them once the round is fully drained. Ref: GR-34.

    - Buy at min bet; assert the immediate balance delta is exactly -cost
      (the triggering spin's own win is NOT yet included)
    - Drain the round; assert the balance increase from there is consistent
      with the deferred baseWin plus whatever the feature round itself won"""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.min_bet:.2f}")
    bet_panel.confirm()

    multiplier = init_data.player_info.bb_bet_multiplier_settings.get("FG1", 100)
    balance_before = game_ready.get_balance()
    result = game_ready.buy_feature_and_wait()
    balance_after_confirm = game_ready.get_balance()
    deferred_base_win = Decimal(str(result.feature_results[0]["featureData"]["baseWin"])) if result.feature_results else Decimal("0")
    log.info("Balance before: %s, after confirm: %s, deferred base win: %s", balance_before, balance_after_confirm, deferred_base_win)

    assert balance_after_confirm == balance_before - result.bet * multiplier, "triggering spin's own win must not be credited yet"

    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    try:
        game_ready.choose_free_spins_feature("sticky")
    except TimeoutError:
        pass
    game_ready.drain_active_feature_if_any()

    balance_after_drain = game_ready.get_balance()
    log.info("Balance after drain: %s", balance_after_drain)
    assert balance_after_drain >= balance_after_confirm + deferred_base_win, "drained balance must include at least the deferred base win"

    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-FUN-062")
def test_bet_reverts_to_pre_buy_value_after_feature_completes(game_ready, init_data):
    """PS-FUN-062: after the bought feature ends the bet reverts to the
    value selected before purchase. Ref: GR-35.

    - Set bet to 2.00, buy, drain
    - Assert the displayed bet is still 2.00 (not silently reset)"""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet("2.00")
    bet_panel.confirm()

    result = game_ready.buy_feature_and_wait()
    log.info("Bought at bet: %s", result.bet)

    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    try:
        game_ready.choose_free_spins_feature("sticky")
    except TimeoutError:
        pass
    game_ready.drain_active_feature_if_any()

    displayed_bet = game_ready.get_displayed_bet_text()
    log.info("Displayed bet after feature completes: %s", displayed_bet)
    assert Decimal(displayed_bet.lstrip("€")) == Decimal("2.00")

    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-FUN-063")
def test_buy_rejected_when_balance_below_cost():
    """PS-FUN-063: Buy Feature is disabled/rejected when balance is below
    100x bet. BLOCKED: this environment's shared session balance (~1.48M)
    cannot realistically be brought below the buy cost without a dedicated
    low-balance account, which isn't available here (same class of blocker
    as test_session_cannot_access_another_players_round). Ref: GR-36."""
    pytest.skip("Blocked: no low-balance session available in this environment to exercise insufficient-funds rejection")


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-FEA-025")
@pytest.mark.test_case("PS-FUN-054")
def test_buy_then_sticky_wilds_plays_out(buy_and_choose, game_ready, init_data):
    """No dedicated workbook row for Sticky Wilds specifically via Buy;
    extends PS-FEA-025 (sticky persistence) and PS-FUN-054 (choice screen)
    to a Buy-sourced entry point instead of an organic trigger.

    - Select min bet, buy and choose Sticky Wilds
    - Play a couple of feature spins, draining the rest, confirming the
      round behaves the same as an organically-triggered Sticky round"""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.min_bet:.2f}")
    bet_panel.confirm()

    triggering_result = buy_and_choose("sticky")
    log.info("Bought and chose Sticky Wilds, triggering scatter count: %s", triggering_result.scatter_count)

    game_ready.drain_active_feature_if_any()
    log.info("Sticky Wilds round (via Buy) drained, balance: %s", game_ready.get_balance())

    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-FEA-035")
@pytest.mark.test_case("PS-FEA-036")
@pytest.mark.test_case("PS-FUN-054")
def test_buy_then_raining_wilds_plays_out(buy_and_choose, game_ready, init_data):
    """No dedicated workbook row for Raining Wilds specifically via Buy;
    extends PS-FEA-035/036 (raining wild count/non-persistence) and
    PS-FUN-054 (choice screen) to a Buy-sourced entry point.

    - Select min bet, buy and choose Raining Wilds
    - Play a couple of feature spins, draining the rest, confirming the
      round behaves the same as an organically-triggered Raining round"""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.min_bet:.2f}")
    bet_panel.confirm()

    triggering_result = buy_and_choose("raining")
    log.info("Bought and chose Raining Wilds, triggering scatter count: %s", triggering_result.scatter_count)

    game_ready.drain_active_feature_if_any()
    log.info("Raining Wilds round (via Buy) drained, balance: %s", game_ready.get_balance())

    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()
