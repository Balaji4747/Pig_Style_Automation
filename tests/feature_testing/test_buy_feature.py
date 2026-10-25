import pytest

pytestmark = [pytest.mark.functional, pytest.mark.regression]

# The entire Buy Feature cluster shares one blocker: the Buy confirm flow's
# network call (endpoint/payload) was never verified (see
# tests/functional/test_buy_free_spins.py, PS-FUN-059/061/062, explicitly
# deferred in the prior session). Every case below needs a successful
# confirm to set up its scenario, so all are Blocked pending that
# groundwork rather than guessing at an unverified flow. The cost-display
# and cancel-path parts (no confirm needed) are already covered by the
# existing tests/functional/test_buy_free_spins.py.


@pytest.mark.test_case("PS-FEA-048")
@pytest.mark.test_case("PS-REG-090")
def test_fs_type_awarded_for_bought_feature():
    """BLOCKED: Buy confirm flow unverified. Ref: GR-32, M-15, M-16 | OBS-10
    (workbook itself also flags whether FS type is chosen in the Buy
    interface or after trigger as unclear)."""
    pytest.skip("Blocked: Buy Feature confirm flow (endpoint/payload) not yet verified")


@pytest.mark.test_case("PS-FEA-049")
@pytest.mark.test_case("PS-REG-091")
def test_bought_feature_always_lands_at_least_3_bn():
    """BLOCKED: Buy confirm flow unverified. Ref: GR-33, M-15, M-16."""
    pytest.skip("Blocked: Buy Feature confirm flow (endpoint/payload) not yet verified")


@pytest.mark.test_case("PS-FEA-050")
@pytest.mark.test_case("PS-REG-092")
def test_double_confirm_debits_only_once():
    """BLOCKED: Buy confirm flow unverified. Ref: GR-33."""
    pytest.skip("Blocked: Buy Feature confirm flow (endpoint/payload) not yet verified")


@pytest.mark.test_case("PS-FEA-051")
@pytest.mark.test_case("PS-REG-093")
def test_refresh_immediately_after_buy_confirm_recovers_feature():
    """BLOCKED: Buy confirm flow unverified (same as PS-INT-005).
    Ref: GR-33, GR-56."""
    pytest.skip("Blocked: Buy Feature confirm flow (endpoint/payload) not yet verified")


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
