import pytest

from utils.megaways_calculator import evaluate, total_win

pytestmark = pytest.mark.boundary


@pytest.mark.test_case("PS-EDG-009")
def test_large_win_displays_full_digits_no_scientific_notation(game_ready):
    """PS-EDG-009: a large win must display with full digits and
    separators, never scientific notation or an overflow glitch. Forces the
    cheat tool's top win tier ("UNBEL WIN") rather than the workbook's exact
    ">= 10,000x bet" (not independently controllable — see DECISIONS.md
    D-008, the same win-tier cheats don't guarantee a specific multiple).
    Ref: GR-25."""
    game_ready.force_next_spin("UNBEL WIN")
    result = game_ready.spin_and_wait()
    assert result.total_win > 0

    displayed_balance = game_ready.get_displayed_balance_text()
    assert displayed_balance and "e" not in displayed_balance.lower(), (
        f"balance display looks like scientific notation: {displayed_balance!r}"
    )
    digit_count = sum(ch.isdigit() for ch in displayed_balance)
    assert digit_count >= len(str(int(result.balance))), "displayed balance has fewer digits than the real balance"


@pytest.mark.test_case("PS-EDG-013")
def test_many_simultaneous_wins_evaluate_and_present_correctly(game_ready):
    """PS-EDG-013 (P1): a spin with wins on several symbols and thousands of
    ways must evaluate and present correctly, with no freeze. Rather than
    force an exact "7 rows all reels" board (not controllable — reel height
    is independently random), this spins until a naturally high-ways result
    occurs (bounded attempts, not an unbounded wait for a specific forced
    outcome) and validates it against the proven calculator oracle.
    Ref: GR-25, GR-01."""
    pay_table = game_ready.get_init_data().game_info.pay_table
    result = None
    for _ in range(10):
        candidate = game_ready.spin_and_wait()
        if candidate.ways >= 1000:
            result = candidate
            break
    assert result is not None, "no spin reached >= 1000 ways in 10 attempts"

    ways = evaluate(result.reel_view, pay_table, result.bet_amount_used)
    assert result.total_win == total_win(ways)
    # The canvas must still be responsive after presenting a complex board.
    assert game_ready.is_pixi_ready()
