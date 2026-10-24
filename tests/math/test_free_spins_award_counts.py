import pytest

# Confirmed from docs/test_cases/math_reference.csv (FG1 Calc / FG2 Calc
# AD3:AE6): bonus-symbol count -> awarded Free Spins, per feature choice.
EXPECTED_AWARDS = {
    (3, "sticky"): 7,
    (4, "sticky"): 12,
    (5, "sticky"): 15,
    (6, "sticky"): 20,
    (3, "raining"): 15,
    (4, "raining"): 18,
    (5, "raining"): 25,
    (6, "raining"): 30,
}

CASES = [
    pytest.param(3, "sticky", id="PS-MTH-038-3BN-sticky", marks=pytest.mark.test_case("PS-MTH-038")),
    pytest.param(4, "sticky", id="PS-MTH-039-4BN-sticky", marks=pytest.mark.test_case("PS-MTH-039")),
    pytest.param(5, "sticky", id="PS-MTH-040-5BN-sticky", marks=pytest.mark.test_case("PS-MTH-040")),
    pytest.param(6, "sticky", id="PS-MTH-041-6BN-sticky", marks=pytest.mark.test_case("PS-MTH-041")),
    pytest.param(3, "raining", id="PS-MTH-042-3BN-raining", marks=pytest.mark.test_case("PS-MTH-042")),
    pytest.param(4, "raining", id="PS-MTH-043-4BN-raining", marks=pytest.mark.test_case("PS-MTH-043")),
    pytest.param(5, "raining", id="PS-MTH-044-5BN-raining", marks=pytest.mark.test_case("PS-MTH-044")),
    pytest.param(6, "raining", id="PS-MTH-045-6BN-raining", marks=pytest.mark.test_case("PS-MTH-045")),
]


@pytest.mark.math
@pytest.mark.regression
@pytest.mark.sanity
@pytest.mark.parametrize("bonus_count, feature", CASES)
def test_bonus_count_awards_correct_free_spins(game_ready, bonus_count, feature):
    """PS-MTH-038..045: the number of awarded Free Spins for each Bonus
    symbol count (3/4/5/6) under each feature choice (Sticky/Raining) must
    match the math file exactly. Ref: docs/test_cases/math_reference.csv
    (FG1 Calc / FG2 Calc AD3:AE6)."""
    game_ready.force_next_spin(f"{bonus_count} OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )

    sticky_spins = game_ready.get_displayed_integer_near_label("titleText", "STICKY WILDS")
    raining_spins = game_ready.get_displayed_integer_near_label("titleText", "RAINING WILDS")
    assert sticky_spins == EXPECTED_AWARDS[(bonus_count, "sticky")]
    assert raining_spins == EXPECTED_AWARDS[(bonus_count, "raining")]

    game_ready.choose_free_spins_feature(feature)
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is None, timeout_ms=10_000
    )
    game_ready.resolve_pending_feature(timeout_ms=120_000)
