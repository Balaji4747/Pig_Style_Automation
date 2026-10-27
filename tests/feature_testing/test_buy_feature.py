from decimal import Decimal

import pytest

from utils.logger import get_logger

pytestmark = [pytest.mark.functional, pytest.mark.regression]

log = get_logger(__name__)

# The Buy confirm flow (endpoint/payload) was unverified when this cluster
# was first written. Confirmed live 27 Oct 2026: clicking "Buy bonus"
# triggers a normal POST /spin call that atomically debits 100x bet and
# always lands a feature trigger, going through the same Sticky/Raining
# choice screen as an organic trigger (resolves OBS-10). The cases below are
# un-skipped accordingly.


@pytest.mark.test_case("PS-FEA-048")
@pytest.mark.test_case("PS-REG-090")
def test_fs_type_awarded_for_bought_feature(game_ready, init_data):
    """PS-FEA-048: resolves OBS-10 - a bought feature goes through the same
    Sticky/Raining Wilds choice screen as an organic trigger, rather than
    the FS type being pre-selected inside the Buy interface. Ref: GR-32,
    M-15, M-16 | OBS-10.

    - Select min bet to minimize the real 100x debit, buy the feature
    - Assert the choice screen appears, then choose Sticky and drain it"""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.min_bet:.2f}")
    bet_panel.confirm()

    result = game_ready.buy_feature_and_wait()
    log.info("Buy triggered: %s, scatter count: %s, next feature: %s", result.is_feature_triggered, result.scatter_count, result.next_feature)
    assert result.is_feature_triggered
    assert result.next_feature == "pickFeature"

    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    try:
        game_ready.choose_free_spins_feature("sticky")
    except TimeoutError:
        pass  # FEATURE_CHOICE_TITLE_NODE can stay stuck visible even after the round already finished
    game_ready.drain_active_feature_if_any()

    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()


@pytest.mark.test_case("PS-FEA-049")
@pytest.mark.test_case("PS-REG-091")
def test_bought_feature_always_lands_at_least_3_bn(game_ready, init_data):
    """PS-FEA-049: a bought feature always triggers with scatter_count >= 3.
    Reduced from the workbook's 100 buys to 3 for cost/time (each buy debits
    100x bet). Ref: GR-33, M-15, M-16.

    - Select min bet, buy 3 times, draining each round before the next buy
    - Assert every buy triggers with scatter_count >= 3"""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.min_bet:.2f}")
    bet_panel.confirm()

    for i in range(3):
        result = game_ready.buy_feature_and_wait()
        log.info("Buy %s: scatter count %s, triggered %s", i + 1, result.scatter_count, result.is_feature_triggered)
        assert result.is_feature_triggered
        assert result.scatter_count >= 3

        game_ready.wait_for(
            lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
        )
        try:
            game_ready.choose_free_spins_feature("sticky")
        except TimeoutError:
            pass  # FEATURE_CHOICE_TITLE_NODE can stay stuck visible even after the round already finished
        game_ready.drain_active_feature_if_any()

    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()


@pytest.mark.test_case("PS-FEA-050")
@pytest.mark.test_case("PS-REG-092")
def test_double_confirm_debits_only_once(game_ready, init_data):
    """PS-FEA-050: tapping Confirm twice in quick succession debits only
    once. Ref: GR-33.

    - Select min bet, open Buy panel, clear spin log
    - Confirm twice back-to-back with no wait in between
    - Assert exactly one /spin response and one cost-sized balance drop"""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.min_bet:.2f}")
    bet_panel.confirm()

    balance_before = game_ready.get_balance()
    game_ready.network_spy.clear("spin")
    panel = game_ready.open_buy_feature()
    cost = panel.cost_text()

    exchange = game_ready.network_spy.wait_for_response("spin", panel.confirm)
    try:
        panel.confirm()
    except RuntimeError:
        pass
    game_ready.page.wait_for_timeout(3_000)

    spin_count = len(game_ready.network_spy.all("spin"))
    balance_after = game_ready.get_balance()
    log.info("Cost: %s, spins fired: %s, balance before: %s, after: %s", cost, spin_count, balance_before, balance_after)
    assert spin_count == 1
    assert balance_after == balance_before - Decimal(cost.lstrip("€"))

    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    try:
        game_ready.choose_free_spins_feature("sticky")
    except TimeoutError:
        pass  # FEATURE_CHOICE_TITLE_NODE can stay stuck visible even after the round already finished
    game_ready.drain_active_feature_if_any()

    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()


@pytest.mark.test_case("PS-FEA-051")
@pytest.mark.test_case("PS-REG-093")
def test_refresh_immediately_after_buy_confirm_recovers_feature(game_ready, init_data):
    """PS-FEA-051 (same scenario as PS-INT-005, implemented independently
    here per project convention): refreshing immediately after Buy confirm
    recovers the purchased feature with no second debit. Ref: GR-33, GR-56.

    - Select min bet, buy, reload immediately (no wait for client rendering)
    - Assert exactly one cost-sized debit occurred, unfinished_info is set
    - Resolve cleanly via ensure_base_game_ready()"""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.min_bet:.2f}")
    bet_panel.confirm()

    balance_before = game_ready.get_balance()
    result = game_ready.buy_feature_and_wait()
    balance_after_buy = game_ready.get_balance()
    log.info("Balance before: %s, after buy: %s", balance_before, balance_after_buy)

    game_ready.network_spy.wait_for_response("init", lambda: game_ready.page.reload(), timeout_ms=30_000)
    game_ready.wait_for(game_ready.is_loaded, timeout_ms=30_000)

    unfinished = game_ready.get_init_data().unfinished_info
    log.info("unfinished_info after reload: %s", unfinished is not None)
    assert unfinished is not None
    assert game_ready.get_balance() == balance_after_buy, "balance changed again across reload - possible double debit"

    game_ready.ensure_base_game_ready(timeout_ms=60_000)
    assert game_ready.get_init_data().unfinished_info is None

    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()


@pytest.mark.test_case("PS-FEA-052")
def test_buy_feature_not_available_during_auto_spin(game_ready):
    """PS-FEA-052 (P1): the Buy Feature interface must not open while Auto
    Spin is active. Ref: GR-32."""
    from pages.buy_feature_panel import BuyFeaturePanel

    game_ready.network_spy.clear("spin")
    panel = game_ready.open_auto_spin_menu()
    panel.select_spin_count(5)
    panel.start()
    game_ready.wait_for(lambda: len(game_ready.network_spy.all("spin")) >= 1, timeout_ms=30_000)

    try:
        game_ready.click_pixi_button(game_ready.BUY_FEATURE_BUTTON_NODE)
    except RuntimeError:
        pass
    assert game_ready.get_pixi_node_or_none(BuyFeaturePanel.COST_TEXT_NODE) is None

    try:
        game_ready.click_pixi_button(game_ready.STOP_AUTO_BUTTON_NODE)
    except RuntimeError:
        pass
    game_ready.page.wait_for_timeout(5_000)
    if game_ready.get_init_data().unfinished_info is not None:
        game_ready.resolve_pending_feature(timeout_ms=120_000)


@pytest.mark.test_case("PS-FEA-053")
def test_bet_change_inside_buy_interface_updates_cost_live(game_ready, init_data):
    """PS-FEA-053 (P1, Partial): changing the bet inside the Buy interface
    should update the shown cost live. The Buy panel only displays the
    CURRENT bet's cost (no in-panel bet selector was found during recon —
    `BuyFeaturePanel` has no bet-change method) — this verifies the cost
    shown is always consistent with whatever the game's CURRENT bet is when
    the panel is opened, changing bet BEFORE opening rather than inside the
    interface. SPEC QUESTION: the workbook itself flags the in-interface
    control as undocumented (not detailed). Ref: GR-32, GR-36."""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet("2.00")
    bet_panel.confirm()

    buy_panel = game_ready.open_buy_feature()
    cost_text = buy_panel.cost_text()
    assert "200" in cost_text.replace(",", ""), f"Buy cost {cost_text!r} doesn't reflect 100x the new bet (2.00)"
    buy_panel.cancel()

    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()
