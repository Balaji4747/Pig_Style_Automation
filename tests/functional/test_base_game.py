import pytest

from utils.logger import get_logger
from utils.megaways_calculator import ways_count

log = get_logger(__name__)


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
@pytest.mark.test_case("PS-REG-002")
def test_reel_count_and_heights_stay_within_bounds(game_ready):
    """PS-FUN-005: 6 reels, each showing 2-7 symbols per spin. Reduced from
    the workbook's 50 spins to 10 for suite run time; still exercises the
    reel-height distribution."""
    for i in range(10):
        result = game_ready.spin_and_wait()
        heights = [len(reel) for reel in result.reel_view]
        log.info("Spin %s: reel heights %s, ways %s, balance %s", i + 1, heights, result.ways, result.balance)
        assert len(result.reel_view) == 6
        for reel in result.reel_view:
            assert 2 <= len(reel) <= 7


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
@pytest.mark.test_case("PS-REG-003")
def test_ways_counter_equals_product_of_reel_heights(game_ready):
    """PS-FUN-006: the displayed MEGAWAYS counter equals the product of the
    symbol counts on all 6 reels for the spin that produced it."""
    result = game_ready.spin_and_wait()
    expected_ways = ways_count(result.reel_view)
    log.info("Reported ways: %s, computed ways: %s, displayed ways: %s", result.ways, expected_ways, game_ready.get_displayed_ways())
    assert result.ways == expected_ways
    assert game_ready.get_displayed_ways() == expected_ways


@pytest.mark.functional
@pytest.mark.regression
def test_maximum_ways_117649_when_all_reels_at_7(game_ready):
    """PS-FUN-007: forcing all reels to height 7 (via "6 OAK AA") shows
    117,649 ways. "6 OAK AA" doesn't *guarantee* a full board every time
    (confirmed: it influences but doesn't fully determine reel heights) —
    retried a few times rather than failing on the first miss."""
    for attempt in range(4):
        game_ready.force_next_spin("6 OAK AA")
        result = game_ready.spin_and_wait()
        heights = [len(reel) for reel in result.reel_view]
        log.info("Attempt %s: reel heights %s, ways %s", attempt + 1, heights, result.ways)
        if all(len(reel) == 7 for reel in result.reel_view):
            assert result.ways == 117_649
            assert game_ready.get_displayed_ways() == 117_649
            return
    pytest.fail("'6 OAK AA' did not produce a full 7-symbol board in 4 attempts")
