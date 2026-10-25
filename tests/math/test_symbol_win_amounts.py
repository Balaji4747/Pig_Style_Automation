from decimal import Decimal

import pytest

from utils.megaways_calculator import evaluate, total_win

# PS-MTH-017..025: specific-symbol win-amount checks. Each forces the named
# cheat outcome and validates the server's totalWin against the proven
# win-math oracle (utils/megaways_calculator, validated against a real
# sample — see CLAUDE.md > Win-calculation test oracle) rather than a
# hand-derived formula, since the cheat tool only forces which symbols can
# land, not the exact resulting ways/wild breakdown (confirmed:
# "6 OAK AA" doesn't even guarantee a 6-of-a-kind win — see
# docs/samples/README.md). This means a few of the workbook's more specific
# phrasings ("BB 5 OAK with 2 on R3", "DD 3 OAK ways 2x2x2") are validated
# generically via the calculator rather than for that exact board shape,
# since forcing an exact ways breakdown isn't possible with the available
# cheat options — the calculator's validation already covers the intent
# (the win formula holds for whatever board actually results).
SYMBOL_CASES = [
    pytest.param(
        "6 OAK AA",
        id="PS-MTH-017-AA-6OAK",
        marks=[pytest.mark.test_case("PS-MTH-017"), pytest.mark.test_case("PS-REG-042")],
    ),
    pytest.param(
        "5 OAK BB ",
        id="PS-MTH-018-BB-5OAK",
        marks=[pytest.mark.test_case("PS-MTH-018"), pytest.mark.test_case("PS-REG-043")],
    ),
    pytest.param("4 OAK CC ", id="PS-MTH-019-CC-4OAK", marks=pytest.mark.test_case("PS-MTH-019")),
    pytest.param(
        "3 OAK DD ",
        id="PS-MTH-020-DD-3OAK",
        marks=[pytest.mark.test_case("PS-MTH-020"), pytest.mark.test_case("PS-REG-044")],
    ),
    pytest.param("6 OAK EE ", id="PS-MTH-021-EE-6OAK", marks=pytest.mark.test_case("PS-MTH-021")),
    pytest.param("4 OAK FF ", id="PS-MTH-022-FF-4OAK", marks=pytest.mark.test_case("PS-MTH-022")),
    pytest.param("5 OAK GG ", id="PS-MTH-023-GG-5OAK", marks=pytest.mark.test_case("PS-MTH-023")),
    pytest.param("5 OAK HH ", id="PS-MTH-023-HH-5OAK", marks=pytest.mark.test_case("PS-MTH-023")),
    pytest.param("5 OAK JJ ", id="PS-MTH-023-JJ-5OAK", marks=pytest.mark.test_case("PS-MTH-023")),
    pytest.param("3 OAK LL ", id="PS-MTH-024-LL-3OAK-min-pay", marks=pytest.mark.test_case("PS-MTH-024")),
]


@pytest.mark.math
@pytest.mark.regression
@pytest.mark.parametrize("outcome", SYMBOL_CASES)
def test_symbol_win_amount_matches_calculator(game_ready, outcome):
    """PS-MTH-017..024: the server's totalWin for a forced symbol outcome
    must match the win-math oracle exactly. Ref: math file BG Calc paytable."""
    game_ready.force_next_spin(outcome)
    pay_table = game_ready.get_init_data().game_info.pay_table
    result = game_ready.spin_and_wait()

    ways = evaluate(result.reel_view, pay_table, result.bet_amount_used)
    assert result.total_win == total_win(ways)


@pytest.mark.math
@pytest.mark.regression
@pytest.mark.test_case("PS-MTH-019")
def test_symbol_win_amount_at_reduced_bet(game_ready):
    """PS-MTH-019: a 4-OAK CC win amount must scale correctly at a
    non-default bet (0.20). Ref: math file BG Calc paytable, bet scaling
    formula (Win = Bet x Pay/20 x Ways)."""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet("0.20")
    bet_panel.confirm()

    game_ready.force_next_spin("4 OAK CC ")
    pay_table = game_ready.get_init_data().game_info.pay_table
    result = game_ready.spin_and_wait()
    assert result.bet == Decimal("0.20")

    ways = evaluate(result.reel_view, pay_table, result.bet_amount_used)
    assert result.total_win == total_win(ways)

    # Resetting the bet is cleanup, not part of this test's claim (already
    # verified above) — confirmed live (D-025) that this reset can still
    # fail to find the target bet label even after open_bet_panel()'s own
    # settle wait (D-024) and select_bet()'s own retry (D-023); fall back
    # to a reload rather than failing an otherwise-passed test over cleanup.
    bet_panel = game_ready.open_bet_panel()
    try:
        bet_panel.select_bet("1.00")
        bet_panel.confirm()
    except RuntimeError:
        game_ready.reload_and_wait_ready()


@pytest.mark.math
@pytest.mark.regression
@pytest.mark.test_case("PS-MTH-025")
def test_symbol_win_amount_at_min_bet_rounding(game_ready, init_data):
    """PS-MTH-025: a 3-OAK KK win at min bet (0.10) must round half-up to 2
    decimals exactly as the oracle computes — this is the case that actually
    exercises rounding (15 * 0.10 / 20 = 0.075 -> 0.08), unlike most other
    symbol/bet combinations which land on an exact 2-decimal value. Ref:
    math file BG Calc paytable, money_rounding (half-up, 2dp)."""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.min_bet:.2f}")
    bet_panel.confirm()

    game_ready.force_next_spin("3 OAK KK ")
    pay_table = game_ready.get_init_data().game_info.pay_table
    result = game_ready.spin_and_wait()

    ways = evaluate(result.reel_view, pay_table, result.bet_amount_used)
    assert result.total_win == total_win(ways)

    # See D-025: resetting the bet is cleanup, not part of this test's
    # claim (already verified above) — fall back to a reload rather than
    # failing an otherwise-passed test over a flaky cleanup click.
    bet_panel = game_ready.open_bet_panel()
    try:
        bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
        bet_panel.confirm()
    except RuntimeError:
        game_ready.reload_and_wait_ready()
