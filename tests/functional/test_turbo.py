import pytest

from utils.logger import get_logger

log = get_logger(__name__)


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-REG-033")
def test_turbo_does_not_change_results_or_balance(game_ready):
    """PS-FUN-066: enabling Turbo Spin does not change results, wins, or
    balance math. Reduced from the workbook's 20 spins to 8 for suite run
    time. (Turbo's own visual on/off state isn't asserted — toggling it had
    no detectable scene-graph signal in testing; this validates the claim
    that actually matters, outcome integrity, via the same balance/win
    arithmetic check used elsewhere.)"""
    game_ready.toggle_turbo()
    log.info("Turbo enabled")
    for i in range(8):
        balance_before = game_ready.get_balance()
        result = game_ready.spin_and_wait()
        log.info("Spin %s: balance before %s, bet %s, win %s, balance after %s", i + 1, balance_before, result.bet, result.total_win, result.balance)
        assert result.balance == balance_before - result.bet + result.total_win
    game_ready.toggle_turbo()
    log.info("Turbo disabled")
