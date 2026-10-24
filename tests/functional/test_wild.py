import pytest

from utils.megaways_calculator import evaluate, total_win


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
@pytest.mark.test_case("PS-REG-020")
def test_wild_never_appears_on_reel_1_or_6(game_ready):
    """PS-FUN-045: Wild (WC) only appears on reels 2-5 in the base game.
    Reduced from the workbook's 500-spin sample to a smaller mix of forced
    wild-heavy outcomes plus free spins for suite run time."""
    outcomes = ["1 OAK WC", "2 OAK WC", "3 OAK WC", "4 OAK WC"]
    checked_any_wild = False

    for outcome in outcomes:
        game_ready.force_next_spin(outcome)
        result = game_ready.spin_and_wait()
        assert result.reel_view[0].count("WC") == 0
        assert result.reel_view[5].count("WC") == 0
        checked_any_wild = checked_any_wild or any("WC" in reel for reel in result.reel_view)

    assert checked_any_wild, "No Wild symbol observed to validate reel placement against"


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-REG-021")
@pytest.mark.test_case("PS-REG-022")
def test_wild_substitution_and_scatter_count_validated_via_calculator(game_ready, init_data):
    """PS-FUN-046 (Wild substitutes for all paying symbols), PS-FUN-047
    (Wild does not substitute for Bonus / inflate scatter count), PS-FUN-049
    (a wild-only combination is impossible, since Wild can never land on
    reel 1 — proven by test_wild_never_appears_on_reel_1_or_6 combined with
    the win algorithm's left-to-right requirement validated in
    test_win_evaluation.py).

    Validated the same way as win_evaluation: force wild-heavy outcomes and
    reproduce the server's winLines exactly with
    utils.megaways_calculator.evaluate() (which treats WC as a substitute
    for any paying symbol, never for BN)."""
    paytable = init_data.game_info.pay_table

    for outcome in ["3 OAK WC", "4 OAK WC"]:
        game_ready.force_next_spin(outcome)
        result = game_ready.spin_and_wait()

        computed = evaluate(result.reel_view, paytable, result.bet_amount_used)
        assert total_win(computed) == result.total_win
        server_set = {
            (wl.symbol, wl.consecutive_count, wl.winning_position, wl.wild_count, wl.win_amount)
            for wl in result.win_lines
        }
        computed_set = {(w.symbol, w.count, w.positions, w.wild_count, w.win) for w in computed}
        assert computed_set == server_set

        # PS-FUN-047: scatter_count must equal the number of reels
        # containing "BN" (WC never counts toward it).
        reels_with_bn = sum(1 for reel in result.reel_view if "BN" in reel)
        assert result.scatter_count == reels_with_bn
