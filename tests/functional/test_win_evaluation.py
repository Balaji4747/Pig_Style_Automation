import pytest

from utils.logger import get_logger
from utils.megaways_calculator import evaluate, total_win

log = get_logger(__name__)

# No cheat involved: force_next_spin() is confirmed unreliable in this
# environment (CLAUDE.md D-019). The win-evaluation algorithm itself
# (left-to-right matching, stop-at-first-non-match, ways multiplication, no
# double-pay, summing multiple symbol wins) is validated by reproducing the
# server's winLines exactly via utils.megaways_calculator.evaluate() on
# whatever board results from genuinely unforced spins - a stronger check
# than any single hand-picked example, and one that doesn't depend on the
# cheat tool actually landing a specific symbol/count.
MAX_SPIN_ATTEMPTS = 30
MIN_WINNING_SAMPLES = 5


def _assert_calculator_matches_server(result, paytable) -> None:
    computed_ways = evaluate(result.reel_view, paytable, result.bet_amount_used, wild_multipliers=result.wild_multipliers)
    log.info("Bet %s: server win %s, computed win %s, balance %s", result.bet, result.total_win, total_win(computed_ways), result.balance)
    assert total_win(computed_ways) == result.total_win

    server_set = {
        (wl.symbol, wl.consecutive_count, wl.winning_position, wl.wild_count, wl.win_amount)
        for wl in result.win_lines
    }
    computed_set = {(w.symbol, w.count, w.positions, w.wild_count, w.win) for w in computed_ways}
    assert computed_set == server_set

    # PS-FUN-041: no winning way below 3-of-a-kind.
    assert all(wl.consecutive_count >= 3 for wl in result.win_lines)
    # PS-FUN-053: Bonus never pays as a way.
    assert all(wl.symbol != "BN" for wl in result.win_lines)


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
@pytest.mark.test_case("PS-REG-014")
@pytest.mark.test_case("PS-REG-015")
@pytest.mark.test_case("PS-REG-016")
@pytest.mark.test_case("PS-REG-017")
@pytest.mark.test_case("PS-REG-018")
@pytest.mark.test_case("PS-REG-019")
def test_win_calculation_matches_server_across_unforced_spins(game_ready, init_data):
    """PS-FUN-038 (left-to-right, adjacent reels only), PS-FUN-039 (stop at
    first non-matching/non-wild reel), PS-FUN-040 (ways = product of
    per-reel match counts), PS-FUN-041 (no pay below 3-of-a-kind),
    PS-FUN-042 (multiple symbol wins summed), PS-FUN-043 (no double-pay of
    a shorter combination inside a longer one).

    - Spin (unforced) up to 30 times, validating the calculator-vs-server
      invariant on every single spin (win or not)
    - Stop early once 5 winning spins have been validated, for a meaningful
      sample of the algorithm actually paying out
    - Fail if zero winning spins were observed within the budget"""
    paytable = init_data.game_info.pay_table
    winning_samples = 0

    for attempt in range(1, MAX_SPIN_ATTEMPTS + 1):
        result = game_ready.spin_and_wait()
        log.info("Attempt %s", attempt)
        _assert_calculator_matches_server(result, paytable)
        if result.win_lines:
            winning_samples += 1
        if winning_samples >= MIN_WINNING_SAMPLES:
            break

    assert winning_samples > 0, f"No winning spin observed in {MAX_SPIN_ATTEMPTS} unforced spins to validate win-evaluation against"


@pytest.mark.functional
@pytest.mark.regression
def test_paytable_pay_increases_with_oak_count(init_data):
    """PS-FUN-044: pay(n+1 OAK) > pay(n OAK) for every symbol.

    - For each paying symbol in the live paytable
    - Assert 3-OAK < 4-OAK < 5-OAK < 6-OAK pay"""
    for symbol, pays in init_data.game_info.pay_table.items():
        three, four, five, six = pays[2], pays[3], pays[4], pays[5]
        if six == 0:
            continue  # non-paying symbols (WC, BN)
        log.info("%s: 3=%s 4=%s 5=%s 6=%s", symbol, three, four, five, six)
        assert three < four < five < six, f"{symbol}: pays not strictly increasing: {pays}"
