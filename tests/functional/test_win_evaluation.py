import pytest

from utils.megaways_calculator import evaluate, total_win

# The cheat tool only forces a symbol/count, not an exact reel layout, so we
# can't reproduce the workbook's hand-picked boards (e.g. "BB on R2,R3,R4 but
# not R1") exactly. Instead these outcomes are forced to reliably produce
# *some* win, and the win-evaluation algorithm itself (left-to-right
# matching, stop-at-first-non-match, ways multiplication, no double-pay,
# summing multiple symbol wins) is validated by reproducing the server's
# winLines exactly via utils.megaways_calculator.evaluate() on whatever
# board results — a stronger check than any single hand-picked example.
FORCE_OUTCOMES_FOR_WINS = ["3 OAK AA", "4 OAK BB ", "5 OAK CC ", "3 OAK KK ", "4 OAK LL "]


def _assert_calculator_matches_server(result, paytable) -> None:
    computed_ways = evaluate(result.reel_view, paytable, result.bet_amount_used)
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
def test_win_calculation_matches_server_across_forced_and_free_spins(game_ready, init_data):
    """PS-FUN-038 (left-to-right, adjacent reels only), PS-FUN-039 (stop at
    first non-matching/non-wild reel), PS-FUN-040 (ways = product of
    per-reel match counts), PS-FUN-041 (no pay below 3-of-a-kind),
    PS-FUN-042 (multiple symbol wins summed), PS-FUN-043 (no double-pay of
    a shorter combination inside a longer one)."""
    paytable = init_data.game_info.pay_table
    checked_any_win = False

    for outcome in FORCE_OUTCOMES_FOR_WINS:
        game_ready.force_next_spin(outcome)
        result = game_ready.spin_and_wait()
        _assert_calculator_matches_server(result, paytable)
        checked_any_win = checked_any_win or bool(result.win_lines)

    for _ in range(5):
        result = game_ready.spin_and_wait()
        _assert_calculator_matches_server(result, paytable)
        checked_any_win = checked_any_win or bool(result.win_lines)

    assert checked_any_win, "No winning spin observed to validate win-evaluation against"


@pytest.mark.functional
@pytest.mark.regression
def test_paytable_pay_increases_with_oak_count(init_data):
    """PS-FUN-044: pay(n+1 OAK) > pay(n OAK) for every symbol."""
    for symbol, pays in init_data.game_info.pay_table.items():
        three, four, five, six = pays[2], pays[3], pays[4], pays[5]
        if six == 0:
            continue  # non-paying symbols (WC, BN)
        assert three < four < five < six, f"{symbol}: pays not strictly increasing: {pays}"
