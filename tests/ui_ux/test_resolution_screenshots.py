import pytest

# PS-UI is fundamentally a visual-regression concern: "no layout jump",
# "legible", "correctly sized/aligned" aren't programmatically checkable
# without either a human reviewing screenshots or a visual-diffing tool this
# project doesn't have set up (see PROGRESS.md). This test captures the one
# thing that IS automatable — confirming the game loads and stays
# interactive (no crash, no blank canvas) at each resolution — and saves a
# screenshot at each for manual review, rather than asserting on things like
# "legible" that can't be graded here.

RESOLUTIONS = [
    pytest.param(1920, 1080, id="PS-UI-002-1920x1080", marks=pytest.mark.test_case("PS-UI-002")),
    pytest.param(1366, 768, id="PS-UI-003-1366x768", marks=pytest.mark.test_case("PS-UI-003")),
    pytest.param(2560, 1080, id="PS-UI-004-2560x1080", marks=pytest.mark.test_case("PS-UI-004")),
    pytest.param(390, 844, id="PS-UI-005-390x844-portrait", marks=pytest.mark.test_case("PS-UI-005")),
    pytest.param(844, 390, id="PS-UI-006-844x390-landscape", marks=pytest.mark.test_case("PS-UI-006")),
]


@pytest.mark.ui
@pytest.mark.parametrize("width, height", RESOLUTIONS)
def test_game_stays_interactive_at_resolution(game_ready, width, height):
    """PS-UI-002..006 (Partial): the base game must stay loaded and
    interactive (reels visible, a spin completes) at each listed resolution,
    with a screenshot saved for manual layout review. Visual correctness
    itself (alignment, no layout jump, legibility) is not asserted here —
    see the module docstring."""
    game_ready.page.set_viewport_size({"width": width, "height": height})
    game_ready.page.wait_for_timeout(1_000)

    assert game_ready.is_base_game_ready()
    result = game_ready.spin_and_wait()
    assert result.closed

    game_ready.screenshot(f"ps_ui_{width}x{height}")

    # Restore a standard desktop viewport for whatever runs next.
    game_ready.page.set_viewport_size({"width": 1280, "height": 720})
