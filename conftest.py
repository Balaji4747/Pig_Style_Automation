pytest_plugins = [
    "fixtures.browser_fixtures",
    "fixtures.game_fixtures",
    "fixtures.network_fixtures",
]


def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default="qa",
        choices=["qa", "staging"],
        help="Environment to run tests against (config/env.yaml)",
    )
