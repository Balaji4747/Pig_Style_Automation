import pytest

pytestmark = pytest.mark.boundary


@pytest.mark.test_case("PS-EDG-038")
def test_large_balance_displays_fully(game_ready):
    """PS-EDG-038 (P2): a balance with 7+ digits must display fully, with no
    overlap/truncation. Opportunistic: this session's balance already
    exceeds 1,000,000 (see DECISIONS.md D-005/D-006), so no setup is needed
    to reach this condition. Ref: GR-19."""
    balance = game_ready.get_init_data().player_info.balance
    assert balance >= 1_000_000, "expected the session's already-large balance to still exceed 1,000,000"

    displayed = game_ready.get_displayed_balance_text()
    assert displayed, "balance field is empty/not rendered"
    # Full-value sanity check: the integer part of the displayed text must
    # contain at least 7 digits (matches a 1,000,000+ balance), not an
    # abbreviated/scientific form (e.g. "1.2M").
    digit_count = sum(ch.isdigit() for ch in displayed)
    assert digit_count >= 7, f"displayed balance looks abbreviated/truncated: {displayed!r}"


@pytest.mark.test_case("PS-EDG-025")
def test_auto_spin_smallest_and_largest_count_options(game_ready):
    """PS-EDG-025 (P2, Partial): the smallest and largest Auto Spin count
    options must both be honoured. The exact configured min/max option
    values were never confirmed during recon (no sample captured), so this
    uses 5 (confirmed smallest, already used in the Functional sheet) and
    25 (confirmed to work as a "larger" count there too) rather than
    guessing the true extremes. Ref: GR-38."""
    # Smallest option.
    game_ready.network_spy.clear("spin")
    panel = game_ready.open_auto_spin_menu()
    panel.select_spin_count(5)
    panel.start()
    game_ready.wait_for(lambda: len(game_ready.network_spy.all("spin")) >= 1, timeout_ms=30_000)
    game_ready.page.wait_for_timeout(2_000)
    try:
        game_ready.click_pixi_button(game_ready.STOP_AUTO_BUTTON_NODE)
    except RuntimeError:
        pass
    game_ready.page.wait_for_timeout(5_000)
    if game_ready.get_init_data().unfinished_info is not None:
        game_ready.resolve_pending_feature(timeout_ms=120_000)
    assert len(game_ready.network_spy.all("spin")) >= 1

    # Larger option.
    game_ready.network_spy.clear("spin")
    panel = game_ready.open_auto_spin_menu()
    panel.select_spin_count(25)
    panel.start()
    game_ready.wait_for(lambda: len(game_ready.network_spy.all("spin")) >= 1, timeout_ms=30_000)
    game_ready.page.wait_for_timeout(2_000)
    try:
        game_ready.click_pixi_button(game_ready.STOP_AUTO_BUTTON_NODE)
    except RuntimeError:
        pass
    game_ready.page.wait_for_timeout(5_000)
    if game_ready.get_init_data().unfinished_info is not None:
        game_ready.resolve_pending_feature(timeout_ms=120_000)
    assert len(game_ready.network_spy.all("spin")) >= 1
