import re
from dataclasses import dataclass
from typing import Optional

from playwright.sync_api import Page, Response


@dataclass
class CapturedExchange:
    url: str
    status: int
    request_body: Optional[dict]
    response_body: Optional[dict]


class NetworkSpy:
    """Captures JSON request/response pairs for game API calls matching named
    URL patterns (e.g. "init", "spin"), so tests can assert on balance/win
    values from the network layer instead of reading canvas pixels.

    Two ways to get a response:
    - wait_for_response(name, trigger): wraps the triggering action (e.g. a
      goto() or a key press) in Playwright's expect_response, so the wait is
      tied to the response caused by *that* action specifically. Preferred
      for single discrete actions like init/spin.
    - last(name)/all(name): a passive page.on("response") listener keeps a
      running log of every matching response regardless of what triggered
      it. Useful for endpoints with no single triggering action to wrap,
      e.g. the Free Spins round's repeated "feature" calls.
    """

    def __init__(self, page: Page, patterns: dict[str, str]):
        self._page = page
        self._patterns = {name: re.compile(pattern) for name, pattern in patterns.items()}
        self._captured: dict[str, list[CapturedExchange]] = {name: [] for name in patterns}
        page.on("response", self._on_response)

    def _on_response(self, response: Response) -> None:
        for name, pattern in self._patterns.items():
            if pattern.search(response.url):
                self._captured[name].append(_to_exchange(response))

    def wait_for_response(self, name: str, trigger, timeout_ms: Optional[float] = None) -> CapturedExchange:
        """Perform `trigger()` (a zero-arg callable) and wait specifically
        for the response it causes to the named endpoint, via Playwright's
        expect_response — not a poll of "last captured", which could race
        with a stale response from an earlier action. The passive
        page.on("response") listener (registered in __init__, so it always
        fires before this method's own handling of the same event) already
        logs the response to last()/all(); this does not log it a second
        time, to avoid duplicate entries."""
        pattern = self._patterns[name]
        with self._page.expect_response(lambda r: bool(pattern.search(r.url)), timeout=timeout_ms) as response_info:
            trigger()
        return _to_exchange(response_info.value)

    def last(self, name: str) -> Optional[CapturedExchange]:
        items = self._captured.get(name, [])
        return items[-1] if items else None

    def all(self, name: str) -> list[CapturedExchange]:
        return list(self._captured.get(name, []))

    def clear(self, name: Optional[str] = None) -> None:
        if name:
            self._captured[name] = []
        else:
            for key in self._captured:
                self._captured[key] = []


def _to_exchange(response: Response) -> CapturedExchange:
    return CapturedExchange(
        url=response.url,
        status=response.status,
        request_body=_safe_json(lambda: response.request.post_data_json),
        response_body=_safe_json(response.json),
    )


def _safe_json(getter):
    try:
        return getter()
    except Exception:
        return None
