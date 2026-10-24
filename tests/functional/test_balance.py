from decimal import Decimal

import pytest


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
def test_balance_debited_by_exactly_the_bet_amount(game_ready):
    """PS-FUN-020: the balance changes by exactly (win - bet) for a single
    paid spin, i.e. the bet is debited exactly once regardless of outcome."""
    balance_before = game_ready.get_balance()
    result = game_ready.spin_and_wait()
    expected_balance = balance_before - result.bet + result.total_win
    assert result.balance == expected_balance


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
def test_base_game_win_credited_to_balance(game_ready):
    """PS-FUN-021: a base game win is credited to the balance. Forces "3 OAK
    AA" (AA on reels 1-3, 1 way) at the default bet (1.00) — math pay:
    15 credits * (1.00 / 20) = 0.75."""
    balance_before = game_ready.get_balance()
    game_ready.force_next_spin("3 OAK AA")
    result = game_ready.spin_and_wait()

    assert result.total_win == Decimal("0.75")
    assert result.balance == balance_before - result.bet + result.total_win


@pytest.mark.functional
@pytest.mark.regression
def test_displayed_balance_matches_api_balance_after_each_round(game_ready):
    """PS-FUN-022: the canvas-displayed balance matches the authoritative
    API balance after every round. Reduced from the workbook's 10 rounds to
    5 for suite run time (there's no separate "wallet backend" to compare
    against in this test environment — the game's own API response is the
    only source of truth available, so this validates UI/API sync)."""
    for _ in range(5):
        result = game_ready.spin_and_wait()
        displayed = Decimal(game_ready.get_displayed_balance_text().lstrip("€").replace(",", ""))
        assert displayed == result.balance
