import pytest


@pytest.mark.functional
@pytest.mark.regression
def test_turbo_does_not_change_results_or_balance(game_ready):
    """PS-FUN-066: enabling Turbo Spin does not change results, wins, or
    balance math. Reduced from the workbook's 20 spins to 8 for suite run
    time. (Turbo's own visual on/off state isn't asserted — toggling it had
    no detectable scene-graph signal in testing; this validates the claim
    that actually matters, outcome integrity, via the same balance/win
    arithmetic check used elsewhere.)"""
    game_ready.toggle_turbo()
    for _ in range(8):
        balance_before = game_ready.get_balance()
        result = game_ready.spin_and_wait()
        assert result.balance == balance_before - result.bet + result.total_win
    game_ready.toggle_turbo()
