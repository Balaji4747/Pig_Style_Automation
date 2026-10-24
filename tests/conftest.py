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
