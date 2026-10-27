from decimal import ROUND_HALF_UP, Decimal

import pytest

from utils.logger import get_logger

log = get_logger(__name__)

# No cheat involved: force_next_spin() is confirmed unreliable in this
# environment (CLAUDE.md D-019), and per explicit instruction this test uses
# genuinely unforced spins rather than trusting any forced outcome. Per
# explicit instruction, this also doesn't insist on one specific symbol/OAK
# count (e.g. "AA 3-OAK") - any symbol, any count is accepted, as long as no
# wild substitution is involved (keeps the payout formula simple: wild
# multipliers are a separate, already-covered concern - see test_wild.py).
# Budget is generous since hunting *any* pure win is common, not rare.
MAX_SPIN_ATTEMPTS = 50


def _spin_until_any_pure_win(game_ready, max_attempts: int = MAX_SPIN_ATTEMPTS):
    """Retries genuinely unforced spins until one contains ANY win line with
    no wild substitution (wild_count == 0) - any symbol, any OAK count.
    Returns (result, matching_win_line, attempts_used), or
    (None, None, max_attempts) if no qualifying spin was observed."""
    for attempt in range(1, max_attempts + 1):
        result = game_ready.spin_and_wait()
        pure_line = next((wl for wl in result.win_lines if wl.wild_count == 0), None)
        if pure_line is not None:
            return result, pure_line, attempt
    return None, None, max_attempts


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
@pytest.mark.test_case("PS-REG-012")
def test_paytable_values_scale_linearly_with_bet(game_ready, init_data):
    """PS-FUN-034: every individual win line's payout equals
    bet * pay(credits) / 20, at full unrounded precision. Validated via
    genuinely unforced spins at min/default/max bet (no cheat tool -
    force_next_spin() is confirmed unreliable, CLAUDE.md D-019). Per explicit
    instruction, accepts whichever symbol/OAK count naturally wins rather
    than insisting on one specific combination (e.g. "AA 3-OAK") - any pure
    (no-wild) win line is a valid sample of the formula. Not read from the
    Paytable UI panel directly (the UI only ever displays the *current*
    bet's scaled values, so reading it at 3 different bets is equivalent to
    - and less reliable than - asserting the formula against real spin
    responses; see test_paytable_ui_reflects_authoritative_values below for
    that coverage).

    Note: confirmed live (27 Oct 2026) that individual win-line amounts are
    NOT rounded to 2 decimals server-side - e.g. at min bet (0.10), a 3-OAK
    win on 15-credit AA pays exactly 0.075, not 0.08. Only the spin's
    aggregate total_win appears to be rounded. This resolves an assumption
    previously flagged as unconfirmed in utils/megaways_calculator.py
    ("per-way vs. per-spin rounding order") - per-way amounts are unrounded.

    - For min, default, and max bet (in that order)
    - Spin (unforced) until any win line with no wild substitution occurs
    - Assert that win line's amount equals the raw, unrounded
      bet * (its symbol's credits for its OAK count) / 20 - distinct from
      the spin's total win, which may include other simultaneous wins
    - Restore the default bet afterward, even if an assertion fails"""
    bets = [init_data.player_info.min_bet, init_data.player_info.default_bet, init_data.player_info.max_bet]
    pay_table = init_data.game_info.pay_table

    try:
        for bet in bets:
            panel = game_ready.open_bet_panel()
            panel.select_bet(f"{bet:.2f}")
            panel.confirm()

            result, win_line, attempts = _spin_until_any_pure_win(game_ready)
            assert result is not None, (
                f"No unforced spin produced any pure (no-wild) win at bet {bet} in {attempts} attempts"
            )
            assert result.bet == bet

            credits = pay_table[win_line.symbol][win_line.consecutive_count - 1]
            # Confirmed live (27 Oct 2026): the server reports each individual
            # win line's amount at full, unrounded precision - only the
            # aggregate total_win is rounded. Compare against the raw,
            # unrounded formula rather than a 2dp-rounded value.
            expected = credits * bet / Decimal(20)
            log.info(
                "Bet %s: %s %s-OAK win found on attempt %s (round %s) - credits %s, expected %s, "
                "actual line win %s, total spin win %s",
                bet, win_line.symbol, win_line.consecutive_count, attempts, result.round_id,
                credits, expected, win_line.win_amount, result.total_win,
            )
            assert win_line.win_amount == expected, (
                f"Incorrect {win_line.symbol} {win_line.consecutive_count}-OAK payout: bet={bet}, "
                f"credits={credits}, expected={expected}, actual={win_line.win_amount}"
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

    AA is used as the representative symbol (matches this test case's own
    focus elsewhere in the suite); both its lowest (3) and highest (6)
    paying tiers are checked to cover a rounding-edge case (3-OAK, at min
    bet) and a round-number case (6-OAK) in the same pass.

    - For min, default, and max bet (in that order)
    - Select the bet, open the Paytable tab
    - Assert AA's displayed 3-OAK and 6-OAK values equal
      credits * bet / 20, rounded half-up, from the authoritative
      init_data paytable (correctness at each distinct bet level is itself
      proof the value updates rather than carrying over stale data, since a
      stale value from a different bet would not independently match the
      newly-expected rounded amount)
    - Close the paytable; assert balance and bet are unaffected by
      opening/closing it
    - Restore the default bet afterward, even if an assertion fails"""
    pay_table = init_data.game_info.pay_table
    bets = [init_data.player_info.min_bet, init_data.player_info.default_bet, init_data.player_info.max_bet]
    symbol = "AA"
    oak_counts = [3, 6]

    try:
        for bet in bets:
            balance_before = game_ready.get_balance()
            bet_panel = game_ready.open_bet_panel()
            bet_panel.select_bet(f"{bet:.2f}")
            bet_panel.confirm()

            paytable = game_ready.open_paytable()
            game_ready.wait_for(paytable.is_displayed, timeout_ms=10_000)

            for count in oak_counts:
                credits = pay_table[symbol][count - 1]
                expected = (credits * bet / Decimal(20)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                displayed = Decimal(paytable.symbol_payout_text(symbol, count).lstrip("€"))
                log.info("Bet %s: %s %s-OAK displayed %s, expected %s", bet, symbol, count, displayed, expected)
                assert displayed == expected, (
                    f"Paytable UI shows wrong value for {symbol} {count}-OAK at bet {bet}: "
                    f"expected {expected}, displayed {displayed}"
                )

            paytable.close()
            assert game_ready.get_balance() == balance_before, "opening/closing the paytable must not change balance"
            displayed_bet = Decimal(game_ready.get_displayed_bet_text().lstrip("€"))
            assert displayed_bet == bet, "opening/closing the paytable must not change the selected bet"
    finally:
        bet_panel = game_ready.open_bet_panel()
        bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
        bet_panel.confirm()
