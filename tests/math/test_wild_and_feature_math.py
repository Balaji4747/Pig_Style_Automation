from decimal import Decimal

import pytest

from utils.megaways_calculator import evaluate

# PS-MTH-027/028/031 (a specific wild multiplier VALUE: x1/x2/x3 only) are
# not forceable — the cheat tool's "<n> OAK WC" options control wild COUNT,
# not which multiplier value results (that's random per the math file's
# weight table), and the task rules explicitly disallow looping random
# spins waiting for a specific outcome. See DECISIONS.md for the full
# reasoning and the Blocked entries for those three IDs.


@pytest.mark.math
@pytest.mark.regression
@pytest.mark.test_case("PS-MTH-029")
@pytest.mark.test_case("PS-MTH-030")
def test_wild_involved_win_has_consistent_structure(game_ready):
    """PS-MTH-029 (two WC on the same way) / PS-MTH-030 (WC and a paying
    symbol on the same reel): forces multiple wilds and checks structural
    correctness of the resulting win lines (ways counted correctly, wild
    count tracked per way, no pay below 3-of-a-kind) via the proven
    ways/structure logic in utils.megaways_calculator.

    Scope note: this does NOT assert exact total_win equality against the
    calculator when a win line's wild_count > 0 — the calculator's
    multiplier handling for wild-involved wins is explicitly flagged as an
    unvalidated ASSUMPTION (no wild-involved sample existed when it was
    built; ways with differing wild multipliers may need a per-way, not
    per-spin, multiplier that evaluate() doesn't model). Asserting monetary
    exactness here risks reporting a calculator gap as a product defect.
    See DECISIONS.md. Ref: math file wild weight table (reels 2-5 only)."""
    game_ready.force_next_spin("3 OAK WC")
    pay_table = game_ready.get_init_data().game_info.pay_table
    result = game_ready.spin_and_wait()

    # Structural check independent of multiplier value: ways/positions must
    # match the calculator's (multiplier-agnostic) structural computation.
    computed_ways = evaluate(result.reel_view, pay_table, result.bet_amount_used)
    computed_structure = {(w.symbol, w.count, w.positions, w.wild_count) for w in computed_ways}
    server_structure = {
        (wl.symbol, wl.consecutive_count, wl.winning_position, wl.wild_count) for wl in result.win_lines
    }
    assert computed_structure == server_structure
    assert all(wl.consecutive_count >= 3 for wl in result.win_lines)

    # Confirmed reel scope from the math file: WC weight is 0 on reels 1/6.
    assert result.reel_view[0].count("WC") == 0
    assert result.reel_view[5].count("WC") == 0


@pytest.mark.math
@pytest.mark.regression
@pytest.mark.test_case("PS-MTH-062")
def test_bonus_symbol_never_appears_during_free_spins(game_ready):
    """PS-MTH-062: the Bonus symbol must never appear on a Free Spins round
    spin's board. Ref: math file FG1/FG2 reel strips (no BN entries)."""
    game_ready.force_next_spin("3 OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    game_ready.choose_free_spins_feature("sticky")
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is None, timeout_ms=10_000
    )
    game_ready.dismiss_congrats_popup_if_present()

    game_ready.network_spy.clear("feature")
    for _ in range(3):
        game_ready.wait_for_loading_overlay_to_clear()
        game_ready.page.wait_for_timeout(5_000)
        try:
            game_ready.network_spy.wait_for_response("feature", game_ready.press_space_bar, timeout_ms=15_000)
        except TimeoutError:
            break

    for exchange in game_ready.network_spy.all("feature"):
        reel_view = exchange.response_body["data"]["result"]["reelView"]
        for reel in reel_view:
            assert "BN" not in reel, "Bonus symbol appeared during a Free Spins round"

    game_ready.resolve_pending_feature(timeout_ms=90_000)


@pytest.mark.math
@pytest.mark.regression
@pytest.mark.test_case("PS-MTH-057")
def test_server_uses_bet_denominator_20(game_ready):
    """PS-MTH-057: the server must evaluate wins using a bet denominator of
    20 (betAmountUsed = bet / 20), matching the math file's "Number of Lines
    Played: 20". Ref: math file Summary."""
    result = game_ready.spin_and_wait()
    assert result.bet_amount_used == (result.bet / Decimal(20))
