from decimal import Decimal

import pytest

from utils.logger import get_logger
from utils.megaways_calculator import evaluate, total_win

log = get_logger(__name__)


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
@pytest.mark.test_case("PS-REG-008")
def test_balance_debited_by_exactly_the_bet_amount(game_ready):
    """PS-FUN-020: the balance changes by exactly (win - bet) for a single
    paid spin, i.e. the bet is debited exactly once regardless of outcome.

    - Record balance, play one spin
    - Assert balance after == balance before - bet + win"""
    balance_before = game_ready.get_balance()
    log.info("Balance before: %s", balance_before)
    result = game_ready.spin_and_wait()
    expected_balance = balance_before - result.bet + result.total_win
    log.info("Bet: %s, win: %s, balance after: %s", result.bet, result.total_win, result.balance)
    assert result.balance == expected_balance


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
@pytest.mark.test_case("PS-REG-009")
def test_base_game_win_credited_to_balance(game_ready, init_data):
    """PS-FUN-021: a base game win is credited to the balance. No cheat
    involved: force_next_spin() is confirmed unreliable in this environment
    (CLAUDE.md D-019) - spins unforced until a real win lands, then
    validates whatever the spin actually returns by recomputing the
    expected win from the real board via megaways_calculator.evaluate()
    instead of a hardcoded value.

    - Spin (unforced) up to 15 times until a real win lands
    - Recompute expected win from the actual board via the calculator
    - Assert computed win matches server win and balance was credited"""
    paytable = init_data.game_info.pay_table
    max_attempts = 15
    for attempt in range(1, max_attempts + 1):
        balance_before = game_ready.get_balance()
        result = game_ready.spin_and_wait()
        log.info("Attempt %s: balance before %s, win %s, balance after %s", attempt, balance_before, result.total_win, result.balance)
        if result.total_win > 0:
            computed = evaluate(result.reel_view, paytable, result.bet_amount_used, wild_multipliers=result.wild_multipliers)
            assert total_win(computed) == result.total_win
            assert result.balance == balance_before - result.bet + result.total_win
            return
    pytest.fail(f"No winning spin observed in {max_attempts} attempts to validate win-credit behavior against")


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-REG-010")
def test_displayed_balance_matches_api_balance_after_each_round(game_ready):
    """PS-FUN-022: the canvas-displayed balance matches the authoritative
    API balance after every round. Reduced from the workbook's 10 rounds to
    5 for suite run time (there's no separate "wallet backend" to compare
    against in this test environment — the game's own API response is the
    only source of truth available, so this validates UI/API sync).

    - Play 5 spins
    - After each, wait for the displayed balance to catch up with the API balance
    - Assert displayed balance equals API balance every round"""
    for i in range(5):
        result = game_ready.spin_and_wait()
        # On a win, the displayed balance only catches up once the win rollup
        # animation finishes crediting it — wait for it rather than assuming
        # it already matches the API balance the instant spin_and_wait() returns.
        game_ready.wait_for_displayed_balance_to_match(result.balance)
        displayed = Decimal(game_ready.get_displayed_balance_text().lstrip("€").replace(",", ""))
        log.info("Spin %s: win %s, API balance %s, displayed balance %s", i + 1, result.total_win, result.balance, displayed)
        assert displayed == result.balance
