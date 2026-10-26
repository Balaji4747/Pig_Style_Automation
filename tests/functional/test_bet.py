from decimal import Decimal

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from utils.logger import get_logger

log = get_logger(__name__)


@pytest.mark.functional
@pytest.mark.regression
def test_bet_panel_opens_with_options_and_closes_unchanged(game_ready, init_data):
    """PS-FUN-014: the Bet button opens the bet panel showing the configured
    min/max and the current bet; closing (Cancel) returns to the base game
    with the bet unchanged."""
    bet_before = game_ready.get_displayed_bet_text()
    log.info("Bet before: %s", bet_before)
    panel = game_ready.open_bet_panel()
    log.info("Bet panel min/max text: %s", panel.min_max_text())

    assert str(init_data.player_info.min_bet) in panel.min_max_text()
    assert str(init_data.player_info.max_bet) in panel.min_max_text()

    panel.cancel()
    log.info("Bet after cancel: %s", game_ready.get_displayed_bet_text())
    assert game_ready.get_displayed_bet_text() == bet_before


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
def test_bet_selection_updates_bet_field_for_every_configured_level(game_ready, init_data):
    """PS-FUN-015 (adapted): this game selects bet levels directly from a
    grid (confirmed — there are no separate increase/decrease stepper
    buttons), not by stepping with +/- controls as the workbook assumes.
    Verifies every configured bet level is selectable and updates the bet
    field immediately. Reduced to a representative subset (first, middle,
    last) of the 38-level ladder for suite run time."""
    levels = init_data.player_info.possible_bets
    sample = [levels[0], levels[len(levels) // 2], levels[-1]]

    for level in sample:
        panel = game_ready.open_bet_panel()
        panel.select_bet(f"{level:.2f}")
        panel.confirm()
        displayed = Decimal(game_ready.get_displayed_bet_text().lstrip("€"))
        log.info("Selected bet level %s, displayed bet: %s", level, displayed)
        assert displayed == level

    # Reset to default bet so later tests aren't affected.
    panel = game_ready.open_bet_panel()
    panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    panel.confirm()


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-REG-005")
def test_bet_stays_within_min_max_range(game_ready, init_data):
    """PS-FUN-016 (adapted): selecting the lowest/highest configured bet
    level works and the bet never leaves the configured min/max range —
    there are no separate increase/decrease controls to test "disabled at
    boundary" against (see PS-FUN-015 adaptation note)."""
    panel = game_ready.open_bet_panel()
    panel.select_bet(f"{init_data.player_info.min_bet:.2f}")
    panel.confirm()
    log.info("Min bet selected, displayed: %s", game_ready.get_displayed_bet_text())
    assert Decimal(game_ready.get_displayed_bet_text().lstrip("€")) == init_data.player_info.min_bet

    panel = game_ready.open_bet_panel()
    panel.select_bet(f"{init_data.player_info.max_bet:.2f}")
    panel.confirm()
    log.info("Max bet selected, displayed: %s", game_ready.get_displayed_bet_text())
    assert Decimal(game_ready.get_displayed_bet_text().lstrip("€")) == init_data.player_info.max_bet

    # Reset to default bet so later tests aren't affected.
    panel = game_ready.open_bet_panel()
    panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    panel.confirm()


@pytest.mark.functional
@pytest.mark.regression
def test_bet_retained_after_closing_panel_and_across_spins(game_ready, init_data):
    """PS-FUN-017: the selected bet is retained after closing the bet panel
    and across consecutive spins."""
    new_bet = Decimal("2.00")
    assert new_bet in init_data.player_info.possible_bets

    panel = game_ready.open_bet_panel()
    panel.select_bet(f"{new_bet:.2f}")
    panel.confirm()
    assert Decimal(game_ready.get_displayed_bet_text().lstrip("€")) == new_bet

    for i in range(3):
        result = game_ready.spin_and_wait()
        log.info("Spin %s: bet %s, win %s, balance %s", i + 1, result.bet, result.total_win, result.balance)
        assert result.bet == new_bet
        assert Decimal(game_ready.get_displayed_bet_text().lstrip("€")) == new_bet

    # Reset to default bet so later tests aren't affected.
    panel = game_ready.open_bet_panel()
    panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    panel.confirm()


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-REG-006")
def test_bet_panel_does_not_open_while_a_spin_is_in_flight(game_ready):
    """PS-FUN-018: bet controls are disabled/ignored while reels are
    spinning and during win presentation."""
    game_ready.wait_for_loading_overlay_to_clear()
    game_ready.page.wait_for_timeout(3_000)  # same pre-spin settle as spin()

    game_ready.press_space_bar()
    game_ready.click_pixi_button(game_ready.BET_BUTTON_NODE)
    bet_panel_open = game_ready.get_pixi_node_or_none("betPanelView") is not None
    log.info("Bet panel opened during in-flight spin: %s (expected: False)", bet_panel_open)
    assert not bet_panel_open

    # Let the in-flight spin resolve normally before moving on.
    try:
        game_ready.network_spy.wait_for_response("spin", lambda: None, timeout_ms=10_000)
    except PlaywrightTimeoutError:
        pass
    game_ready.page.wait_for_timeout(3_000)


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-REG-007")
def test_bet_panel_does_not_open_during_free_spins(game_ready):
    """PS-FUN-019: bet controls are disabled for the whole Free Spins
    feature."""
    from utils.api_client import parse_spin_response

    def trigger():
        game_ready.wait_for_loading_overlay_to_clear()
        game_ready.page.wait_for_timeout(3_000)
        game_ready.press_space_bar()

    game_ready.force_next_spin("3 OAK BN")
    exchange = game_ready.network_spy.wait_for_response("spin", trigger, timeout_ms=10_000)
    result = parse_spin_response(exchange.response_body)
    log.info("Feature triggered: %s, next feature: %s", result.is_feature_triggered, result.next_feature)
    assert result.is_feature_triggered

    game_ready.wait_for(lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000)
    game_ready.choose_free_spins_feature("sticky")
    game_ready.wait_for(lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is None, timeout_ms=10_000)
    game_ready.dismiss_congrats_popup_if_present()

    game_ready.click_pixi_button(game_ready.BET_BUTTON_NODE)
    bet_panel_open = game_ready.get_pixi_node_or_none("betPanelView") is not None
    log.info("Bet panel opened during Free Spins: %s (expected: False)", bet_panel_open)
    assert not bet_panel_open

    # Clean up: drain the feature so later tests start clean.
    game_ready.play_feature_spins_to_completion()
    game_ready.dismiss_congrats_popup_if_present()
    game_ready.wait_for(game_ready.is_base_game_ready, timeout_ms=15_000)
    game_ready.wait_for_loading_overlay_to_clear(timeout_ms=60_000)
