import time

import pytest

from utils.logger import get_logger

log = get_logger(__name__)


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
@pytest.mark.test_case("PS-REG-034")
def test_auto_spin_plays_exact_count_then_stops(game_ready):
    """PS-FUN-072: Auto Spin plays exactly the selected number of spins then
    stops automatically. Uses the smallest available count (5) for suite
    run time."""
    balance_before = game_ready.get_balance()
    log.info("Balance before: %s", balance_before)

    game_ready.network_spy.clear("spin")
    panel = game_ready.open_auto_spin_menu()
    panel.select_spin_count(5)
    panel.start()
    log.info("Auto Spin started: 5 spins selected")

    last_count, stable_since = -1, None
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        game_ready.page.wait_for_timeout(1_000)
        count = len(game_ready.network_spy.all("spin"))
        if count != last_count:
            log.info("Spins completed so far: %s", count)
        if count == last_count:
            if stable_since is None:
                stable_since = time.monotonic()
            elif time.monotonic() - stable_since > 5:
                break
        else:
            stable_since = None
        last_count = count

    spin_count = len(game_ready.network_spy.all("spin"))
    balance_after = game_ready.get_balance()
    log.info("Auto Spin finished: %s spins, balance after: %s", spin_count, balance_after)
    assert spin_count == 5


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-REG-035")
def test_auto_spin_stop_ends_after_current_round(game_ready):
    """PS-FUN-074: pressing Stop ends Auto Spin after the current round
    completes; no further rounds start."""
    balance_before = game_ready.get_balance()
    log.info("Balance before: %s", balance_before)

    game_ready.network_spy.clear("spin")
    panel = game_ready.open_auto_spin_menu()
    panel.select_spin_count(25)
    panel.start()
    log.info("Auto Spin started: 25 spins selected")

    game_ready.wait_for(lambda: len(game_ready.network_spy.all("spin")) >= 2, timeout_ms=30_000)
    log.info("Spins so far: %s - clicking Stop", len(game_ready.network_spy.all("spin")))
    game_ready.click_pixi_button(game_ready.STOP_AUTO_BUTTON_NODE)

    game_ready.page.wait_for_timeout(5_000)
    count_after_stop = len(game_ready.network_spy.all("spin"))
    log.info("Spins at Stop: %s", count_after_stop)
    game_ready.page.wait_for_timeout(5_000)
    final_count = len(game_ready.network_spy.all("spin"))
    balance_after = game_ready.get_balance()
    log.info("Final spin count: %s, balance after: %s", final_count, balance_after)
    assert final_count == count_after_stop


@pytest.mark.functional
@pytest.mark.regression
def test_auto_spin_cancel_does_not_start_spins(game_ready):
    """PS-FUN-075: Cancel in the Auto Spin menu closes it without starting
    any spins or debiting."""
    balance_before = game_ready.get_balance()
    log.info("Balance before: %s", balance_before)

    game_ready.network_spy.clear("spin")
    panel = game_ready.open_auto_spin_menu()
    panel.select_spin_count(25)
    panel.cancel()
    log.info("Auto Spin menu cancelled")

    game_ready.page.wait_for_timeout(3_000)
    spin_count = len(game_ready.network_spy.all("spin"))
    balance_after = game_ready.get_balance()
    log.info("Spins fired: %s, balance after: %s", spin_count, balance_after)
    assert spin_count == 0
    assert balance_after == balance_before


@pytest.mark.functional
@pytest.mark.regression
def test_bet_panel_does_not_open_during_auto_spin(game_ready):
    """PS-FUN-079: bet controls are disabled during Auto Spin."""
    balance_before = game_ready.get_balance()
    log.info("Balance before: %s", balance_before)

    panel = game_ready.open_auto_spin_menu()
    panel.select_spin_count(5)
    panel.start()
    log.info("Auto Spin started: 5 spins selected")
    game_ready.wait_for(lambda: len(game_ready.network_spy.all("spin")) >= 1, timeout_ms=30_000)
    log.info("Spins so far: %s - attempting to open Bet panel", len(game_ready.network_spy.all("spin")))

    game_ready.click_pixi_button(game_ready.BET_BUTTON_NODE)
    bet_panel_open = game_ready.get_pixi_node_or_none("betPanelView") is not None
    log.info("Bet panel opened: %s (expected: False)", bet_panel_open)
    assert not bet_panel_open

    try:
        game_ready.click_pixi_button(game_ready.STOP_AUTO_BUTTON_NODE)
    except RuntimeError:
        pass
    game_ready.page.wait_for_timeout(5_000)
    log.info("Balance after: %s", game_ready.get_balance())
