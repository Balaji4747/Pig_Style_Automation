from decimal import ROUND_HALF_UP, Decimal

import pytest

from utils.logger import get_logger
from utils.megaways_calculator import evaluate, total_win

log = get_logger(__name__)

# No cheat involved: force_next_spin() is confirmed unreliable in this
# environment (CLAUDE.md D-019). No filtering on symbol/OAK count/wild
# involvement either - the first win of any shape at all is accepted and
# validated immediately via the project's own wild-aware calculator oracle,
# rather than hunting for a specific narrower pattern.
MAX_SPIN_ATTEMPTS = 30


def _spin_until_any_win(game_ready, max_attempts: int = MAX_SPIN_ATTEMPTS):
    """Retries genuinely unforced spins until any win occurs at all - any
    symbol, any OAK count, wild-involved or not. Returns
    (result, attempts_used), or (None, max_attempts) if no win landed."""
    for attempt in range(1, max_attempts + 1):
        result = game_ready.spin_and_wait()
        if result.total_win > 0:
            return result, attempt
    return None, max_attempts


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
@pytest.mark.test_case("PS-REG-012")
def test_paytable_values_scale_linearly_with_bet(game_ready, init_data):
    """PS-FUN-034: real spin payouts match the documented formula
    (bet * pay(credits) / 20, summed per way, wild multipliers applied)
    at every bet level. Validated via genuinely unforced spins (no cheat
    tool - force_next_spin() is confirmed unreliable, CLAUDE.md D-019).
    Takes the first win of any shape at all (no filtering on symbol/OAK
    count/wild involvement) and validates it immediately via the project's
    own wild-aware calculator oracle (utils/megaways_calculator.evaluate()),
    rather than hunting for one specific narrower pattern. Not read from the
    Paytable UI panel directly (the UI only ever displays the *current*
    bet's scaled values, so reading it at 3 different bets is equivalent to
    - and less reliable than - asserting the formula against real spin
    responses; see test_paytable_ui_reflects_authoritative_values below for
    that coverage).

    - For min, default, and max bet (in that order)
    - Spin (unforced) until any win occurs at all
    - Recompute the win from the real board via the calculator and assert
      it exactly matches the server's total_win, then move on"""
    bets = [init_data.player_info.min_bet, init_data.player_info.default_bet, init_data.player_info.max_bet]
    pay_table = init_data.game_info.pay_table

    try:
        for bet in bets:
            panel = game_ready.open_bet_panel()
            panel.select_bet(f"{bet:.2f}")
            panel.confirm()

            result, attempts = _spin_until_any_win(game_ready)
            assert result is not None, f"No unforced spin produced any win at bet {bet} in {attempts} attempts"
            assert result.bet == bet

            computed = evaluate(result.reel_view, pay_table, result.bet_amount_used, wild_multipliers=result.wild_multipliers)
            log.info(
                "Bet %s: win found on attempt %s (round %s) - server win %s, computed win %s",
                bet, attempts, result.round_id, result.total_win, total_win(computed),
            )
            assert total_win(computed) == result.total_win, (
                f"Incorrect payout at bet={bet}: server total_win={result.total_win}, computed={total_win(computed)}"
            )
    finally:
        panel = game_ready.open_bet_panel()
        panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
        panel.confirm()


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-FUN-034")
def test_paytable_ui_reflects_authoritative_values_at_min_default_max_bet(game_ready, init_data):
    """Paytable UI validation: per-symbol values update correctly with bet,
    are correctly rounded/formatted, and match the authoritative paytable.

    Confirmed live (27 Oct 2026): the Paytable UI
    (.symbol-payout-grid .treasure-item[data-symbol]/.level-row/
    .points-amount, pages/paytable_page.py) displays a CURRENCY value
    already scaled to the current bet, rounded HALF-UP to 2 decimals (e.g.
    AA 3-OAK at bet 0.10: 15 * 0.10 / 20 = 0.075 displays as "€0.08") - the
    opposite rounding behavior from individual spin win-line amounts, which
    are unrounded (see test_paytable_values_scale_linearly_with_bet above).
    UI display rounds; the raw API win-line values don't.

    Full combinatorial coverage, not a representative sample: every
    configured bet level (all of init_data.player_info.possible_bets, not
    just min/default/max) x every paying symbol (AA-LL, excludes WC/BN which
    never pay) x every OAK tier (3/4/5/6). No live spins involved here (pure
    UI reading against the already-known authoritative paytable), so this
    full scale is cheap - no cheat-tool/randomness concerns apply.

    - For every configured bet level
    - Select the bet, open the Paytable tab
    - For every paying symbol and every OAK tier, assert the displayed value
      equals credits * bet / 20, rounded half-up, from the authoritative
      init_data paytable
    - Close the paytable; assert balance and bet are unaffected by
      opening/closing it
    - Restore the default bet afterward, even if an assertion fails"""
    pay_table = init_data.game_info.pay_table
    bets = init_data.player_info.possible_bets
    symbols = [s for s, pays in pay_table.items() if pays[5] != 0]  # excludes WC, BN (never pay)
    oak_counts = [3, 4, 5, 6]

    try:
        for bet in bets:
            balance_before = game_ready.get_balance()
            bet_panel = game_ready.open_bet_panel()
            bet_panel.select_bet(f"{bet:.2f}")
            bet_panel.confirm()

            paytable = game_ready.open_paytable()
            game_ready.wait_for(paytable.is_displayed, timeout_ms=10_000)

            for symbol in symbols:
                for count in oak_counts:
                    credits = pay_table[symbol][count - 1]
                    expected = (credits * bet / Decimal(20)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    displayed = Decimal(paytable.symbol_payout_text(symbol, count).lstrip("€"))
                    assert displayed == expected, (
                        f"Paytable UI shows wrong value for {symbol} {count}-OAK at bet {bet}: "
                        f"expected {expected}, displayed {displayed}"
                    )
            log.info("Bet %s: all %s symbol/tier combinations correct", bet, len(symbols) * len(oak_counts))

            paytable.close()
            assert game_ready.get_balance() == balance_before, "opening/closing the paytable must not change balance"
            displayed_bet = Decimal(game_ready.get_displayed_bet_text().lstrip("€"))
            assert displayed_bet == bet, "opening/closing the paytable must not change the selected bet"
    finally:
        bet_panel = game_ready.open_bet_panel()
        bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
        bet_panel.confirm()
