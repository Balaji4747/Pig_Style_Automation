import pytest

from utils.network_spy import NetworkSpy


@pytest.fixture
def network_spy(page, config) -> NetworkSpy:
    """Captures init/spin API requests and responses for the current test's page."""
    return NetworkSpy(page, config["network_patterns"])
