from decimal import Decimal

import pytest

from utils.megaways_calculator import evaluate, total_win


@pytest.mark.math
def test_wild_involved_way_is_scaled_by_the_active_wild_multiplier():
    """Regression test for D-025/D-035: locks in the exact scenario first
    captured live, where a wild_count=1 way paid double its base amount
    while a non-wild way of the same symbol/count stayed at its base
    amount. Mirrors the real captured sample's shape (one wild-involved
    3-OAK BB way at double, one plain 3-OAK BB way at base), with
    wild_multipliers reporting a 2x multiplier."""
    reel_view = [
        ["BB", "AA", "CC"],
        ["BB", "WC", "DD"],
        ["BB", "EE", "FF"],
    ]
    paytable = {"BB": [0, 0, Decimal("0.5"), Decimal("1"), Decimal("2"), Decimal("3")]}

    ways = evaluate(reel_view, paytable, bet_amount_used=Decimal("1"), wild_multipliers=[[1, 4, 2]])

    assert len(ways) == 2
    by_wild_count = {w.wild_count: w for w in ways}
    assert by_wild_count[0].win == Decimal("0.50")
    assert by_wild_count[1].win == Decimal("1.00")
    assert total_win(ways) == Decimal("1.50")


@pytest.mark.math
def test_non_wild_way_is_unaffected_by_an_active_wild_multiplier_elsewhere():
    """A way with wild_count=0 must NOT be scaled even if some other way in
    the same spin involved a wild — matches the confirmed D-025 sample
    (two non-wild 0.5 ways stayed exactly 0.5 while the wild-involved way
    alone doubled)."""
    reel_view = [
        ["BB", "AA"],
        ["BB", "DD"],
        ["BB", "EE"],
    ]
    paytable = {"BB": [0, 0, Decimal("0.5"), Decimal("1"), Decimal("2"), Decimal("3")]}

    ways = evaluate(reel_view, paytable, bet_amount_used=Decimal("1"), wild_multipliers=[[1, 4, 2]])

    assert len(ways) == 1
    assert ways[0].wild_count == 0
    assert ways[0].win == Decimal("0.50")


@pytest.mark.math
def test_zero_entry_in_wild_multipliers_is_treated_as_no_multiplier():
    """A raw wild_multipliers entry of 0 (seen in a real non-winning sample,
    docs/samples/spin_response.json) must not zero out a win — 0 is not a
    valid wild-multiplier value per the math file's x1/x2/x3 range, so it's
    treated as 1x (no effect)."""
    reel_view = [["BB", "AA"], ["BB", "DD"], ["WC", "EE"]]
    paytable = {"BB": [0, 0, Decimal("0.5"), Decimal("1"), Decimal("2"), Decimal("3")]}

    ways = evaluate(reel_view, paytable, bet_amount_used=Decimal("1"), wild_multipliers=[[3, 2, 0]])

    assert len(ways) == 1
    assert ways[0].win == Decimal("0.50")


@pytest.mark.math
def test_no_wild_multipliers_behaves_exactly_as_before():
    """Omitting wild_multipliers (or passing an empty list) must reproduce
    the pre-D-025-fix behaviour exactly, for any existing caller that
    doesn't pass it."""
    reel_view = [["BB", "AA"], ["BB", "DD"], ["BB", "EE"]]
    paytable = {"BB": [0, 0, Decimal("0.5"), Decimal("1"), Decimal("2"), Decimal("3")]}

    ways = evaluate(reel_view, paytable, bet_amount_used=Decimal("1"))

    assert len(ways) == 1
    assert ways[0].win == Decimal("0.50")
