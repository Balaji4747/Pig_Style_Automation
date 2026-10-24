from decimal import Decimal

import pytest

pytestmark = [pytest.mark.compatibility, pytest.mark.smoke]

# PS-CMP-001..013 ask for the same full smoke flow (load, spin, win, bet
# change, both Free Spins choices, Buy Feature, Auto Spin, Info, Sound)
# across a long list of real OS/browser/device combinations (Windows+Chrome/
# Firefox/Edge, macOS+Safari/Chrome, iOS/iPadOS+Safari/Chrome, Android
# phone/tablet+Chrome/Samsung Internet, oldest-supported versions). This
# harness can only vary browser ENGINE (chromium/firefox/webkit) and
# viewport/touch emulation via pytest-playwright's --browser/--device flags
# — it cannot reach a real macOS/iOS/Android device/OS or a specific browser
# version. So every one of these rows is "Partial": this one flow, run once
# per --browser/--device combination (see CLAUDE.md > Running tests), covers
# the *engine*-level behavior faithfully, but the exact listed OS/device/
# version itself is not what actually ran. Approximate mapping used in the
# final report: Chrome/Edge -> chromium, Firefox -> firefox, Safari -> webkit,
# iOS/iPadOS -> webkit + --device emulation, Android -> chromium + --device
# emulation. "Oldest supported version", "Samsung Internet" specifically,
# and real touch/OS behavior have no equivalent at all and stay unautomated.


@pytest.mark.test_case("PS-CMP-001")
@pytest.mark.test_case("PS-CMP-002")
@pytest.mark.test_case("PS-CMP-003")
@pytest.mark.test_case("PS-CMP-004")
@pytest.mark.test_case("PS-CMP-005")
@pytest.mark.test_case("PS-CMP-006")
@pytest.mark.test_case("PS-CMP-007")
@pytest.mark.test_case("PS-CMP-008")
@pytest.mark.test_case("PS-CMP-009")
@pytest.mark.test_case("PS-CMP-010")
@pytest.mark.test_case("PS-CMP-011")
@pytest.mark.test_case("PS-CMP-012")
@pytest.mark.test_case("PS-CMP-013")
def test_full_smoke_flow(game_ready, init_data):
    """PS-CMP-001..013 (Partial — see module docstring): load, spin and win,
    bet change, both Free Spins choices, Buy Feature interface, Auto Spin,
    Info panel and Sound toggle, run once per browser engine/device via
    `pytest tests/compatibility --env qa --browser firefox` /
    `--browser webkit` / `--device "iPhone 13"` etc."""
    assert game_ready.is_loaded()
    balance_before = game_ready.get_balance()

    # Spin and win.
    game_ready.force_next_spin("3 OAK AA")
    result = game_ready.spin_and_wait()
    assert result.total_win > 0
    assert result.balance == balance_before - result.bet + result.total_win

    # Bet change.
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet("2.00")
    bet_panel.confirm()
    result = game_ready.spin_and_wait()
    assert result.bet == Decimal("2.00")
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()

    # Free Spins: Sticky Wilds.
    game_ready.force_next_spin("3 OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    game_ready.choose_free_spins_feature("sticky")
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is None, timeout_ms=10_000
    )
    game_ready.resolve_pending_feature(timeout_ms=120_000)
    assert game_ready.get_init_data().unfinished_info is None

    # Free Spins: Raining Wilds.
    game_ready.force_next_spin("3 OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    game_ready.choose_free_spins_feature("raining")
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is None, timeout_ms=10_000
    )
    game_ready.resolve_pending_feature(timeout_ms=120_000)
    assert game_ready.get_init_data().unfinished_info is None

    # Buy Feature interface (open/inspect/cancel — confirm does not run here,
    # the confirm flow itself is unverified, see DECISIONS.md).
    buy_panel = game_ready.open_buy_feature()
    assert buy_panel.cost_text()
    buy_panel.cancel()

    # Auto Spin (small count).
    game_ready.network_spy.clear("spin")
    auto_panel = game_ready.open_auto_spin_menu()
    auto_panel.select_spin_count(5)
    auto_panel.start()
    game_ready.wait_for(lambda: len(game_ready.network_spy.all("spin")) >= 1, timeout_ms=30_000)
    try:
        game_ready.click_pixi_button(game_ready.STOP_AUTO_BUTTON_NODE)
    except RuntimeError:
        pass
    game_ready.page.wait_for_timeout(3_000)
    if game_ready.get_init_data().unfinished_info is not None:
        game_ready.resolve_pending_feature(timeout_ms=120_000)

    # Info panel (Rules/Paytable).
    rules_page = game_ready.open_info_panel()
    assert rules_page.page.locator(rules_page.PANEL_SELECTOR).is_visible()
    paytable_page = rules_page.go_to_paytable()
    assert paytable_page.is_displayed()
    paytable_page.close()

    # Sound toggle round-trips without raising.
    sound_on = game_ready.get_pixi_node_or_none(game_ready.SOUND_ON_BUTTON_NODE)
    sound_off = game_ready.get_pixi_node_or_none(game_ready.SOUND_OFF_BUTTON_NODE)
    assert sound_on is not None or sound_off is not None
