import pytest

from utils.config_loader import load_config

# Confirmed (24 Oct 2026): the game serves a genuinely different portrait
# layout on mobile (vertically stacked controls below the reels, not a
# scaled-down desktop view) — but the same named PIXI scene-graph nodes,
# just repositioned, so BasePage's PIXI-node click strategy works unchanged.
# Run against it with pytest-playwright's own built-in device emulation,
# e.g.: pytest --env qa -m smoke --device "iPhone 13"


@pytest.fixture(scope="session")
def env_name(pytestconfig) -> str:
    return pytestconfig.getoption("--env")


@pytest.fixture(scope="session")
def config(env_name) -> dict:
    return load_config(env_name)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, config, pytestconfig):
    # pytest-playwright's own browser_context_args already merges in the
    # chosen device's viewport/isMobile/hasTouch/userAgent when --device is
    # passed — don't clobber that with the desktop config viewport.
    if pytestconfig.getoption("--device", default=None):
        return browser_context_args
    viewport = config["viewport"]
    return {
        **browser_context_args,
        "viewport": {"width": viewport["width"], "height": viewport["height"]},
    }
