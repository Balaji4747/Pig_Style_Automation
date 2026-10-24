import pytest


@pytest.mark.smoke
def test_game_loads_balance_visible_and_spin_updates_balance(game_ready):
    """PS-FUN-001: game loads, balance is visible, and one spin completes
    with balance updated by exactly (win - bet)."""
    game_page = game_ready
    assert game_page.is_loaded()

    balance_before = game_page.get_balance()
    assert balance_before is not None

    spin_result = game_page.spin_and_wait()
    expected_balance = round(balance_before - spin_result.bet + spin_result.total_win, 2)

    assert spin_result.balance == pytest.approx(expected_balance, abs=0.01)
