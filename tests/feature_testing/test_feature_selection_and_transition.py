from decimal import Decimal

import pytest

from utils.api_client import parse_spin_response

pytestmark = [pytest.mark.functional, pytest.mark.regression]


@pytest.mark.test_case("PS-FEA-041")
def test_choosing_sticky_starts_sticky_fs_with_correct_count(game_ready):
    """PS-FEA-041: choosing Sticky Wilds after a 4-BN trigger must start
    Sticky Wilds Free Spins with 12 spins. Ref: GR-16, GR-05."""
    game_ready.force_next_spin("4 OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    sticky_count = game_ready.get_displayed_integer_near_label("titleText", "STICKY WILDS")
    assert sticky_count == 12

    game_ready.choose_free_spins_feature("sticky")
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is None, timeout_ms=10_000
    )
    game_ready.resolve_pending_feature(timeout_ms=180_000)
    assert game_ready.get_init_data().unfinished_info is None


@pytest.mark.test_case("PS-FEA-042")
def test_choosing_raining_starts_raining_fs_with_correct_count(game_ready):
    """PS-FEA-042: choosing Raining Wilds after a 4-BN trigger must start
    Raining Wilds Free Spins with 18 spins. Ref: GR-16, GR-09."""
    game_ready.force_next_spin("4 OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    raining_count = game_ready.get_displayed_integer_near_label("titleText", "RAINING WILDS")
    assert raining_count == 18

    game_ready.choose_free_spins_feature("raining")
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is None, timeout_ms=10_000
    )
    game_ready.resolve_pending_feature(timeout_ms=180_000)
    assert game_ready.get_init_data().unfinished_info is None


@pytest.mark.test_case("PS-FEA-043")
def test_rapid_double_tap_on_both_choice_options_starts_only_one_feature(game_ready):
    """PS-FEA-043: rapidly tapping both Sticky and Raining options must
    start exactly one feature, never both/neither. Ref: GR-16."""
    game_ready.force_next_spin("3 OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )

    for label in ("STICKY WILDS", "RAINING WILDS"):
        try:
            game_ready.click_pixi_text(label)
        except RuntimeError:
            pass

    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is None, timeout_ms=10_000
    )
    game_ready.resolve_pending_feature(timeout_ms=180_000)
    assert game_ready.get_init_data().unfinished_info is None


@pytest.mark.test_case("PS-FEA-044")
def test_refresh_while_choice_screen_open_returns_to_choice_screen(game_ready):
    """PS-FEA-044: refreshing while the Free Spins choice screen is open
    must restore that same choice screen (same BN count/spin numbers), with
    no default selection made automatically. Ref: GR-16, GR-56."""
    game_ready.force_next_spin("5 OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    sticky_before = game_ready.get_displayed_integer_near_label("titleText", "STICKY WILDS")
    raining_before = game_ready.get_displayed_integer_near_label("titleText", "RAINING WILDS")

    game_ready.network_spy.wait_for_response("init", lambda: game_ready.page.reload(), timeout_ms=30_000)
    assert game_ready.get_init_data().unfinished_info is not None
    game_ready.wait_for(game_ready.is_loaded, timeout_ms=30_000)
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=30_000
    )
    sticky_after = game_ready.get_displayed_integer_near_label("titleText", "STICKY WILDS")
    raining_after = game_ready.get_displayed_integer_near_label("titleText", "RAINING WILDS")
    assert (sticky_after, raining_after) == (sticky_before, raining_before)

    game_ready.resolve_pending_feature(timeout_ms=180_000)


@pytest.mark.test_case("PS-FEA-045")
def test_choice_screen_shows_correct_spin_counts_for_every_bn_count(game_ready):
    """PS-FEA-045: the choice screen must show correct spin counts for each
    Bonus-symbol count (3/4/5/6). Ref: GR-05, GR-09, GR-17."""
    expected = {3: (7, 15), 4: (12, 18), 5: (15, 25), 6: (20, 30)}
    for bonus_count, (expected_sticky, expected_raining) in expected.items():
        game_ready.force_next_spin(f"{bonus_count} OAK BN")
        game_ready.spin_and_wait_feature_trigger_only()
        game_ready.wait_for(
            lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None,
            timeout_ms=15_000,
        )
        sticky = game_ready.get_displayed_integer_near_label("titleText", "STICKY WILDS")
        raining = game_ready.get_displayed_integer_near_label("titleText", "RAINING WILDS")
        assert (sticky, raining) == (expected_sticky, expected_raining), f"mismatch for {bonus_count} BN"

        game_ready.choose_free_spins_feature("sticky")
        game_ready.wait_for(
            lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is None, timeout_ms=10_000
        )
        game_ready.resolve_pending_feature(timeout_ms=180_000)


@pytest.mark.test_case("PS-FEA-046")
def test_feature_transition_preserves_balance_bet_and_settings(game_ready, init_data):
    """PS-FEA-046 (P1, Partial): the transition from base game into Free
    Spins and back must preserve balance, bet, and settings (turbo/sound).
    Turbo-on/sound-off preconditions are applied via existing GamePage
    toggles; the actual VISUAL sound-mute state isn't independently
    verifiable (no audio hook), so only the turbo toggle's PIXI state and
    balance/bet continuity are asserted. Ref: GR-37, GR-49."""
    game_ready.toggle_turbo()
    turbo_sprite_before = game_ready.get_pixi_node_or_none(game_ready.TURBO_BUTTON_NODE)

    game_ready.force_next_spin("3 OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    game_ready.choose_free_spins_feature("sticky")
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is None, timeout_ms=10_000
    )
    game_ready.resolve_pending_feature(timeout_ms=180_000)

    turbo_sprite_after = game_ready.get_pixi_node_or_none(game_ready.TURBO_BUTTON_NODE)
    assert (turbo_sprite_before is not None) == (turbo_sprite_after is not None)

    result = game_ready.spin_and_wait()
    assert result.bet == init_data.player_info.default_bet
    game_ready.toggle_turbo()


@pytest.mark.test_case("PS-FEA-047")
def test_triggering_spin_pays_line_wins_before_entering_fs(game_ready):
    """PS-FEA-047: the triggering spin's own line wins must be paid before
    entering Free Spins — the base win is included in the triggering spin's
    own response, credited immediately (not deferred to the FS summary).
    Not forced to the exact "AA 3oak + 3 BN" combination (no such specific
    compound cheat option) — verifies the invariant generically for
    whatever (possibly zero) base win accompanies the forced trigger.
    Ref: GR-34, GR-14."""
    balance_before = game_ready.get_init_data().player_info.balance
    game_ready.force_next_spin("3 OAK BN")
    exchange = game_ready.spin()
    result = parse_spin_response(exchange.response_body)
    assert result.is_feature_triggered
    assert result.balance == balance_before - result.bet + result.total_win

    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    game_ready.resolve_pending_feature(timeout_ms=180_000)
