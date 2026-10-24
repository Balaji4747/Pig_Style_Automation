import pytest


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
@pytest.mark.test_case("PS-REG-024")
def test_three_bonus_symbols_trigger_free_spins(game_ready):
    """PS-FUN-050: 3 Bonus symbols anywhere on the reels trigger Free Spins
    (the FS type selection screen). force_next_spin("3 OAK BN") places BN on
    3 separate reels (non-adjacent is irrelevant — Bonus is a scatter, not a
    ways symbol)."""
    game_ready.force_next_spin("3 OAK BN")
    result = game_ready.spin_and_wait()
    assert result.scatter_count >= 3
    assert result.is_feature_triggered
    assert result.next_feature == "pickFeature"


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-REG-025")
def test_fewer_than_three_bonus_symbols_do_not_trigger(game_ready):
    """PS-FUN-051: fewer than 3 Bonus symbols do not trigger Free Spins.
    Validated as an emergent property across a batch of regular spins (the
    cheat tool only forces 3-6 OAK BN, not exactly 2) — scatter_count < 3
    must always mean is_feature_triggered is False."""
    checked_any_scatter_below_three = False
    for _ in range(8):
        result = game_ready.spin_and_wait()
        if result.scatter_count < 3:
            assert not result.is_feature_triggered
            checked_any_scatter_below_three = True
    assert checked_any_scatter_below_three, "No spin with <3 scatters observed in this sample"


@pytest.mark.functional
@pytest.mark.regression
def test_bonus_symbols_do_not_pay_as_a_way(game_ready):
    """PS-FUN-053: Bonus symbols never award a ways pay (BN pay is 0 in the
    math file, confirmed in config/paytable.yaml and the live paytable)."""
    game_ready.force_next_spin("3 OAK BN")
    result = game_ready.spin_and_wait()
    assert all(wl.symbol != "BN" for wl in result.win_lines)
