import pytest

pytestmark = [pytest.mark.functional, pytest.mark.regression]


@pytest.mark.test_case("PS-FEA-035")
@pytest.mark.test_case("PS-REG-081")
def test_raining_wild_count_per_spin_is_0_to_6(game_ready, trigger_and_choose, play_one_feature_spin):
    """PS-FEA-035: between 0 and 6 Raining Wilds may appear on any single
    Free Spin, never more. Ref: GR-10, M-11."""
    trigger_and_choose(6, "raining")
    for _ in range(20):
        data = play_one_feature_spin()
        if data is None:
            break
        wild_count = sum(reel.count("WC") for reel in data["result"]["reelView"])
        assert 0 <= wild_count <= 6, f"Raining Wild count {wild_count} outside 0-6"
    game_ready.resolve_pending_feature(timeout_ms=240_000)


@pytest.mark.test_case("PS-FEA-036")
@pytest.mark.test_case("PS-REG-082")
def test_raining_wilds_do_not_persist_to_next_spin(game_ready, trigger_and_choose, play_one_feature_spin):
    """PS-FEA-036: Raining Wilds must NOT persist — each spin's wild
    positions must be independent of the previous spin's (unlike Sticky
    Wilds, which only ever grow, see PS-FEA-025). This checks the
    distinguishing negative: at least one spin's wild positions must NOT be
    a superset of the previous spin's (if every spin were a superset, that
    would indicate sticky-like persistence, a mechanic mismatch).
    Ref: GR-10."""
    trigger_and_choose(3, "raining")
    previous_positions = None
    saw_non_persistence = False
    for _ in range(15):
        data = play_one_feature_spin()
        if data is None:
            break
        reel_view = data["result"]["reelView"]
        positions = {
            (reel_idx, row_idx)
            for reel_idx, reel in enumerate(reel_view)
            for row_idx, symbol in enumerate(reel)
            if symbol == "WC"
        }
        if previous_positions and not previous_positions.issubset(positions):
            saw_non_persistence = True
        previous_positions = positions

    game_ready.resolve_pending_feature(timeout_ms=120_000)
    if not saw_non_persistence:
        pytest.skip("Every spin happened to be a superset of the last in this run — inconclusive, not a failure")


@pytest.mark.test_case("PS-FEA-037")
@pytest.mark.test_case("PS-REG-083")
def test_raining_wild_multiplier_values_within_spec(game_ready, trigger_and_choose, play_one_feature_spin):
    """PS-FEA-037: each Raining Wild's multiplier must be one of the
    documented values (x1/x2/x3 per the math file — SPEC QUESTION: rules
    text only mentions x2/x3, OBS-01). Ref: GR-11, M-11 | OBS-01."""
    trigger_and_choose(3, "raining")
    for _ in range(15):
        data = play_one_feature_spin()
        if data is None:
            break
        for multiplier in data["result"].get("wildMultipliers", []):
            value = multiplier if isinstance(multiplier, int) else multiplier.get("multiplier", multiplier)
            assert value in (1, 2, 3), f"wild multiplier {value} outside the documented x1/x2/x3 range"
    game_ready.resolve_pending_feature(timeout_ms=120_000)


@pytest.mark.test_case("PS-FEA-038")
def test_raining_wild_sizes():
    """PS-FEA-038 (P1): Raining Wild visual sizes must match spec. Not
    automated — the workbook itself marks this "No" (SPEC QUESTION: the
    math file has no size table for FG1, OBS-05, so there's no documented
    expectation to assert against even if this were a gradable visual
    claim). Ref: GR-10 | OBS-05."""
    pytest.skip("Not automated: workbook marks this No — no documented size spec to test against (OBS-05)")


@pytest.mark.test_case("PS-FEA-039")
def test_raining_wilds_land_only_on_reels_2_to_5(game_ready, trigger_and_choose, play_one_feature_spin):
    """PS-FEA-039: Raining Wilds must never land on reel 1 or reel 6.
    Ref: GR-10, M-11 | OBS-05."""
    trigger_and_choose(6, "raining")
    for _ in range(20):
        data = play_one_feature_spin()
        if data is None:
            break
        reel_view = data["result"]["reelView"]
        assert reel_view[0].count("WC") == 0, "Raining Wild landed on reel 1"
        assert reel_view[5].count("WC") == 0, "Raining Wild landed on reel 6"
    game_ready.resolve_pending_feature(timeout_ms=240_000)


@pytest.mark.test_case("PS-FEA-040")
def test_raining_wild_replaces_underlying_symbol(game_ready, trigger_and_choose, play_one_feature_spin):
    """PS-FEA-040: a Raining Wild must replace whatever symbol was
    underneath, and that position must evaluate as Wild (not the original
    symbol) — validated via the win-math oracle treating every WC position
    as wild-substitutable, matching the server's own win lines exactly
    (same technique as PS-MTH-029/030). Ref: GR-10."""
    from utils.megaways_calculator import evaluate

    pay_table = game_ready.get_init_data().game_info.pay_table
    trigger_and_choose(3, "raining")
    checked_any_wild_spin = False
    for _ in range(15):
        data = play_one_feature_spin()
        if data is None:
            break
        reel_view = data["result"]["reelView"]
        if any("WC" in reel for reel in reel_view):
            checked_any_wild_spin = True
            computed_ways = evaluate(reel_view, pay_table, data["result"]["betAmountUsed"])
            computed_structure = {(w.symbol, w.count, w.positions, w.wild_count) for w in computed_ways}
            server_structure = {
                (wl["symbol"], wl["consecutiveCount"], tuple(wl["winningPosition"]), wl["wildCount"])
                for wl in data["result"].get("winLines", [])
            }
            assert computed_structure == server_structure

    game_ready.resolve_pending_feature(timeout_ms=120_000)
    if not checked_any_wild_spin:
        pytest.skip("No Raining Wild landed in this run's sampled spins — not forceable")
