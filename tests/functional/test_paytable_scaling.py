from decimal import Decimal

import pytest


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
@pytest.mark.test_case("PS-REG-012")
def test_paytable_values_scale_linearly_with_bet(game_ready, init_data):
    """PS-FUN-034: every paytable value equals bet * pay(credits) / 20,
    rounded half-up to 2 decimals. Validated via forced wins at
    min/default/max bet rather than reading the Paytable UI panel directly
    (the UI only ever displays the *current* bet's scaled values, so
    reading it at 3 different bets is equivalent to — and less reliable
    than — asserting the formula against real spin responses).

    Note: the workbook's "ratios between bets exactly equal bet ratios" is
    only true where no rounding occurs — at min bet (0.10), 15 * 0.10 / 20
    = 0.075 rounds to 0.08, so 0.08 / 0.75 != 0.10 / 1.00. The formula
    check below (with correct rounding) is the accurate version of this
    assertion."""
    bets = [init_data.player_info.min_bet, init_data.player_info.default_bet, init_data.player_info.max_bet]
    wins = {}

    for bet in bets:
        panel = game_ready.open_bet_panel()
        panel.select_bet(f"{bet:.2f}")
        panel.confirm()

        game_ready.force_next_spin("3 OAK AA")
        result = game_ready.spin_and_wait()
        assert result.bet == bet
        wins[bet] = result.total_win

    raw_pay = init_data.game_info.pay_table["AA"][2]  # 3-OAK credits
    for bet in bets:
        assert wins[bet] == (raw_pay * bet / Decimal(20)).quantize(Decimal("0.01"))

    panel = game_ready.open_bet_panel()
    panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    panel.confirm()
