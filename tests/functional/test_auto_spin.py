import time

import pytest


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
@pytest.mark.test_case("PS-REG-034")
def test_auto_spin_plays_exact_count_then_stops(game_ready):
    """PS-FUN-072: Auto Spin plays exactly the selected number of spins then
    stops automatically. Uses the smallest available count (5) for suite
    run time."""
    game_ready.network_spy.clear("spin")
    panel = game_ready.open_auto_spin_menu()
    panel.select_spin_count(5)
    panel.start()

    last_count, stable_since = -1, None
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        game_ready.page.wait_for_timeout(1_000)
        count = len(game_ready.network_spy.all("spin"))
        if count == last_count:
            if stable_since is None:
                stable_since = time.monotonic()
            elif time.monotonic() - stable_since > 5:
                break
        else:
            stable_since = None
        last_count = count

    assert len(game_ready.network_spy.all("spin")) == 5


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-REG-035")
def test_auto_spin_stop_ends_after_current_round(game_ready):
    """PS-FUN-074: pressing Stop ends Auto Spin after the current round
    completes; no further rounds start."""
    game_ready.network_spy.clear("spin")
    panel = game_ready.open_auto_spin_menu()
    panel.select_spin_count(25)
    panel.start()

    game_ready.wait_for(lambda: len(game_ready.network_spy.all("spin")) >= 2, timeout_ms=30_000)
    game_ready.click_pixi_button(game_ready.STOP_AUTO_BUTTON_NODE)

    game_ready.page.wait_for_timeout(5_000)
    count_after_stop = len(game_ready.network_spy.all("spin"))
    game_ready.page.wait_for_timeout(5_000)
    assert len(game_ready.network_spy.all("spin")) == count_after_stop


@pytest.mark.functional
@pytest.mark.regression
def test_auto_spin_cancel_does_not_start_spins(game_ready):
    """PS-FUN-075: Cancel in the Auto Spin menu closes it without starting
    any spins or debiting."""
    balance_before = game_ready.get_balance()
    game_ready.network_spy.clear("spin")
    panel = game_ready.open_auto_spin_menu()
    panel.select_spin_count(25)
    panel.cancel()

    game_ready.page.wait_for_timeout(3_000)
    assert len(game_ready.network_spy.all("spin")) == 0
    assert game_ready.get_balance() == balance_before


@pytest.mark.functional
@pytest.mark.regression
def test_bet_panel_does_not_open_during_auto_spin(game_ready):
    """PS-FUN-079: bet controls are disabled during Auto Spin."""
    panel = game_ready.open_auto_spin_menu()
    panel.select_spin_count(5)
    panel.start()
    game_ready.wait_for(lambda: len(game_ready.network_spy.all("spin")) >= 1, timeout_ms=30_000)

    game_ready.click_pixi_button(game_ready.BET_BUTTON_NODE)
    assert game_ready.get_pixi_node_or_none("betPanelView") is None

    try:
        game_ready.click_pixi_button(game_ready.STOP_AUTO_BUTTON_NODE)
    except RuntimeError:
        pass
    game_ready.page.wait_for_timeout(5_000)
