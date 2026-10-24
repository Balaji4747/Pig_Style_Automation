import pytest

from pages.game_page import GamePage
from utils.api_client import InitResponse


@pytest.fixture
def game_ready(page, config, network_spy) -> GamePage:
    """Navigates to the game, waits for it to load (canvas present and the
    init API response captured), and dismisses the splash screen so the
    caller lands directly on the playable base game."""
    game_page = GamePage(page, network_spy)
    game_page.goto(config["game_url"], timeout_ms=config["timeouts"]["game_ready_ms"])
    game_page.wait_for(game_page.is_loaded, timeout_ms=config["timeouts"]["game_ready_ms"])
    game_page.ensure_base_game_ready(timeout_ms=config["timeouts"]["game_ready_ms"])
    return game_page


@pytest.fixture
def init_data(game_ready: GamePage) -> InitResponse:
    """Parsed init response (real paytable, bet limits, currency, RTP, opCnf
    flags, unfinishedInfo) captured when the game loaded, so tests can assert
    against the session's actual values instead of hardcoding them."""
    return game_ready.get_init_data()
