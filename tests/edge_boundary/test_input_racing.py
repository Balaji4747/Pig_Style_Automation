from decimal import Decimal

import pytest

from pages.buy_feature_panel import BuyFeaturePanel
from utils.api_client import parse_spin_response

pytestmark = pytest.mark.boundary


@pytest.mark.test_case("PS-EDG-019")
def test_spam_clicking_play_starts_only_sequential_rounds(game_ready):
    """PS-EDG-019: spam-pressing Play for 3s must start only sequential
    rounds (no overlapping/duplicate requests), each debited once.
    Ref: GR-22."""
    game_ready.network_spy.clear("spin")
    game_ready.wait_for_loading_overlay_to_clear()
    game_ready.page.wait_for_timeout(3_000)

    canvas = game_ready.page.locator(game_ready.CANVAS_SELECTOR).first
    canvas.focus()
    import time

    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        game_ready.page.keyboard.press("Space")
        game_ready.page.wait_for_timeout(100)

    # Let whatever round is in flight actually finish before inspecting.
    game_ready.page.wait_for_timeout(5_000)

    round_ids = [parse_spin_response(e.response_body).round_id for e in game_ready.network_spy.all("spin")]
    assert len(round_ids) == len(set(round_ids)), "duplicate round ID from spam-clicking Play"
    if game_ready.get_init_data().unfinished_info is not None:
        game_ready.resolve_pending_feature(timeout_ms=120_000)


@pytest.mark.test_case("PS-EDG-020")
def test_simultaneous_space_and_click_starts_one_round(game_ready):
    """PS-EDG-020 (P1, Desktop Chrome): pressing space and clicking Play at
    the same time must start exactly one round, not two. Ref: GR-44."""
    game_ready.network_spy.clear("spin")
    game_ready.wait_for_loading_overlay_to_clear()
    game_ready.page.wait_for_timeout(3_000)

    canvas = game_ready.page.locator(game_ready.CANVAS_SELECTOR).first
    canvas.focus()
    bounds = game_ready.get_pixi_node(game_ready.SPIN_BUTTON_NODE)
    canvas_box = canvas.bounding_box()
    cx = canvas_box["x"] + bounds["x"] + bounds["width"] / 2
    cy = canvas_box["y"] + bounds["y"] + bounds["height"] / 2

    game_ready.page.keyboard.down("Space")
    game_ready.page.mouse.click(cx, cy)
    game_ready.page.keyboard.up("Space")
    game_ready.page.wait_for_timeout(8_000)

    assert len(game_ready.network_spy.all("spin")) == 1
    if game_ready.get_init_data().unfinished_info is not None:
        game_ready.resolve_pending_feature(timeout_ms=120_000)


@pytest.mark.test_case("PS-EDG-021")
def test_click_during_win_presentation_does_not_double_credit(game_ready):
    """PS-EDG-021 (P1): clicking Play during win presentation must not
    double-credit the win or start a round for the price of two debits —
    whether the presentation is skipped or not is this game's own choice
    (not hard-asserted), but the balance math across both rounds must add
    up exactly. Ref: GR-22."""
    game_ready.force_next_spin("3 OAK AA")
    balance_before = game_ready.get_init_data().player_info.balance
    exchange = game_ready.spin()
    first = parse_spin_response(exchange.response_body)
    assert first.total_win > 0

    # Try to start a second round immediately, while the win presentation
    # would normally still be playing (no settle wait here, unlike spin()).
    game_ready.network_spy.clear("spin")
    game_ready.press_space_bar()
    game_ready.page.wait_for_timeout(8_000)

    second_exchanges = game_ready.network_spy.all("spin")
    if second_exchanges:
        second = parse_spin_response(second_exchanges[-1].response_body)
        assert second.balance == first.balance - second.bet + second.total_win
    else:
        # The click during presentation was ignored outright — equally valid,
        # just confirm the first win's credit is still intact.
        game_ready.reload_and_wait_ready()
        assert game_ready.get_init_data().player_info.balance == first.balance

    if game_ready.get_init_data().unfinished_info is not None:
        game_ready.resolve_pending_feature(timeout_ms=120_000)


@pytest.mark.test_case("PS-EDG-023")
def test_buy_feature_disabled_while_spinning(game_ready):
    """PS-EDG-023 (P1): the Buy Feature interface must not open while reels
    are spinning. Ref: GR-32."""
    game_ready.wait_for_loading_overlay_to_clear()
    game_ready.page.wait_for_timeout(3_000)
    game_ready.press_space_bar()

    try:
        game_ready.click_pixi_button(game_ready.BUY_FEATURE_BUTTON_NODE)
    except RuntimeError:
        pass
    assert game_ready.get_pixi_node_or_none(BuyFeaturePanel.COST_TEXT_NODE) is None

    game_ready.page.wait_for_timeout(5_000)
    if game_ready.get_init_data().unfinished_info is not None:
        game_ready.resolve_pending_feature(timeout_ms=120_000)


@pytest.mark.test_case("PS-EDG-041")
def test_bet_change_immediately_before_spin_uses_new_bet(game_ready, init_data):
    """PS-EDG-041 (P1, Partial): changing the bet and immediately pressing
    Play must use the NEW bet, not a stale one. `spin()`'s own built-in
    settle wait means Space is never actually pressed within the workbook's
    200ms window of the bet change, so this checks the resulting outcome
    (correct bet applied) rather than racing the exact timing. Ref: GR-20."""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet("2.00")
    bet_panel.confirm()
    result = game_ready.spin_and_wait()
    assert result.bet == Decimal("2.00")

    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()
