import pytest

from pages.game_page import GamePage
from utils.network_spy import NetworkSpy


@pytest.fixture
def open_game_page_in(config):
    """Factory for opening an independent GamePage (its own page + network
    spy) against the shared session token, on a given BrowserContext — used
    by interruption/edge cases that need a *second*, separate page object
    rather than the single one the `game_ready` fixture already provides
    (close/reopen, browser-crash, multi-tab scenarios)."""

    def _factory(context) -> GamePage:
        page = context.new_page()
        network_spy = NetworkSpy(page, config["network_patterns"])
        game_page = GamePage(page, network_spy)
        game_page.goto(config["game_url"], timeout_ms=config["timeouts"]["game_ready_ms"])
        game_page.wait_for(game_page.is_loaded, timeout_ms=config["timeouts"]["game_ready_ms"])
        game_page.ensure_base_game_ready(timeout_ms=config["timeouts"]["game_ready_ms"])
        return game_page

    return _factory


@pytest.fixture
def buy_and_choose(game_ready):
    """Buys the feature and chooses the given variant - the Buy-entry
    counterpart to tests/feature_testing/conftest.py's trigger_and_choose().
    Lives here (not tests/feature_testing/conftest.py) since it's used by
    tests/functional/, tests/feature_testing/ and tests/interruption/ alike.
    Does not depend on force_next_spin() (confirmed non-functional, D-019):
    buying is a real, deterministic purchase."""

    def _do(which: str):
        triggering_result = game_ready.buy_feature_and_wait()
        game_ready.wait_for(
            lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None,
            timeout_ms=15_000,
        )
        # choose_free_spins_feature()'s own completion check polls
        # FEATURE_CHOICE_TITLE_NODE's visibility - confirmed live (27 Oct
        # 2026) that this flag can stay stuck true even after the choice was
        # submitted and the whole FS round already played out to its
        # Congratulations popup (the same stale-visible-forever quirk
        # documented for this node elsewhere, e.g. resolve_pending_feature's
        # docstring). Tolerate a timeout here rather than treat the round
        # having already finished as a failure.
        try:
            game_ready.choose_free_spins_feature(which)
        except TimeoutError:
            pass
        game_ready.dismiss_congrats_popup_if_present()
        return triggering_result

    return _do
