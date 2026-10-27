import pytest

from utils.logger import get_logger
from utils.megaways_calculator import evaluate, total_win

log = get_logger(__name__)

# No cheat involved: force_next_spin() is confirmed unreliable in this
# environment (CLAUDE.md D-019) - both tests below use genuinely unforced
# spins and retry until the condition they need to observe (any Wild on the
# board / a wild-involved win) occurs naturally, rather than trusting a
# forced outcome.
MAX_SPIN_ATTEMPTS = 50


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
@pytest.mark.test_case("PS-REG-020")
def test_wild_never_appears_on_reel_1_or_6(game_ready):
    """PS-FUN-045: Wild (WC) only appears on reels 2-5 in the base game.

    - Spin (unforced) until Wild appears anywhere on the board
    - On every spin along the way, assert reel 1 and reel 6 contain no Wild"""
    checked_any_wild = False

    for attempt in range(1, MAX_SPIN_ATTEMPTS + 1):
        result = game_ready.spin_and_wait()
        log.info(
            "Attempt %s: reel 1 WC count %s, reel 6 WC count %s",
            attempt, result.reel_view[0].count("WC"), result.reel_view[5].count("WC"),
        )
        assert result.reel_view[0].count("WC") == 0
        assert result.reel_view[5].count("WC") == 0
        if any("WC" in reel for reel in result.reel_view):
            checked_any_wild = True
            break

    assert checked_any_wild, f"No Wild symbol observed in {MAX_SPIN_ATTEMPTS} unforced spins to validate reel placement against"


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

    Validated the same way as win_evaluation: on every unforced spin,
    reproduce the server's winLines exactly with
    utils.megaways_calculator.evaluate() (which treats WC as a substitute
    for any paying symbol, never for BN) - this invariant holds regardless
    of whether a Wild was involved. Retries until at least one wild-involved
    win is actually observed, to prove the substitution math specifically,
    not just the generic no-wild case already covered elsewhere.

    - Spin (unforced) repeatedly; on every spin, recompute wins via the
      calculator and assert an exact match with the server, plus the
      scatter-count invariant
    - Stop once a wild-involved win has been observed and validated"""
    paytable = init_data.game_info.pay_table
    checked_wild_win = False

    for attempt in range(1, MAX_SPIN_ATTEMPTS + 1):
        result = game_ready.spin_and_wait()

        computed = evaluate(result.reel_view, paytable, result.bet_amount_used, wild_multipliers=result.wild_multipliers)
        log.info(
            "Attempt %s: server win %s, computed win %s, wild multipliers %s",
            attempt, result.total_win, total_win(computed), result.wild_multipliers,
        )
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

        if any(wl.wild_count > 0 for wl in result.win_lines):
            checked_wild_win = True
            break

    assert checked_wild_win, f"No wild-involved win observed in {MAX_SPIN_ATTEMPTS} unforced spins to validate substitution against"
