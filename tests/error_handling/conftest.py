import re

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from pages.game_page import GamePage
from utils.network_spy import CapturedExchange, NetworkSpy


@pytest.fixture
def mock_spin_failure(game_ready, config):
    """Routes the next spin request through a given Playwright route handler
    (an abort, or a fulfill() with a failure status/body), triggers exactly
    one spin attempt, and returns the CapturedExchange if a response came
    back or None if the request was aborted outright. Shared by every
    PS-ERR case that mocks a server/network failure on the spin endpoint,
    since they only differ in which handler they install and what they
    assert about the aftermath."""
    pattern = re.compile(config["network_patterns"]["spin"])

    def _do(handler, timeout_ms: int = 8_000) -> CapturedExchange | None:
        game_ready.page.route(pattern, handler)
        try:
            try:
                return game_ready.spin(timeout_ms=timeout_ms)
            except PlaywrightTimeoutError:
                return None
        finally:
            game_ready.page.unroute(pattern, handler)

    return _do


@pytest.fixture
def open_game_page_blocking_assets(config):
    """Opens a fresh game page with requests to common game-asset file types
    (images/audio/atlases) aborted — for simulating "assets fail to load"
    (PS-ERR-014/015). The exact real asset URL pattern wasn't captured
    during recon, so this blocks by file extension instead, which is
    guaranteed to cover every image/audio asset regardless of path."""
    _ASSET_PATTERN = re.compile(r"\.(png|jpe?g|webp|mp3|ogg|wav|atlas|ktx|basis)(\?|$)", re.IGNORECASE)

    def _factory(context):
        page = context.new_page()
        page.route(_ASSET_PATTERN, lambda route: route.abort())
        network_spy = NetworkSpy(page, config["network_patterns"])
        game_page = GamePage(page, network_spy)
        return game_page, _ASSET_PATTERN

    return _factory
