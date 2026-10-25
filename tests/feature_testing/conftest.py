import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


@pytest.fixture
def trigger_and_choose(game_ready):
    """Forces a Bonus trigger with the given count, chooses the given
    feature, and returns the triggering SpinResult — the common setup every
    PS-FEA case needs before inspecting Free Spins behavior."""

    def _do(bonus_count: int, which: str):
        game_ready.force_next_spin(f"{bonus_count} OAK BN")
        triggering_result = game_ready.spin_and_wait_feature_trigger_only()
        game_ready.wait_for(
            lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None,
            timeout_ms=15_000,
        )
        game_ready.choose_free_spins_feature(which)
        game_ready.wait_for(
            lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is None, timeout_ms=10_000
        )
        game_ready.dismiss_congrats_popup_if_present()
        return triggering_result

    return _do


@pytest.fixture
def play_one_feature_spin(game_ready):
    """Plays exactly one Free Spins round spin (with the proven settle-wait
    budget) and returns its raw response dict, or None if the round is
    already over. Used by PS-FEA cases that need to inspect individual
    spins rather than drain the whole round at once."""

    def _do(response_timeout_ms: int = 15_000):
        game_ready.dismiss_congrats_popup_if_present()
        game_ready.wait_for_loading_overlay_to_clear()
        game_ready.page.wait_for_timeout(5_000)
        try:
            exchange = game_ready.network_spy.wait_for_response(
                "feature", game_ready.press_space_bar, timeout_ms=response_timeout_ms
            )
        except PlaywrightTimeoutError:
            return None
        return exchange.response_body["data"]

    return _do
