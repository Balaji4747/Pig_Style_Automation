import pytest


@pytest.fixture
def raw_fetch(game_ready):
    """Fires a raw same-origin fetch() from inside the page itself (so the
    browser attaches the same cookies/credentials a real request would) —
    used for STR cases that need to send a request the game's own JS would
    never normally send (concurrent duplicates, out-of-context calls,
    tampered URLs), where no UI action can produce it. Returns
    {status, ok, body} as a dict (body is parsed JSON if possible, else the
    raw text)."""

    def _fetch(url: str, method: str = "POST") -> dict:
        return game_ready.page.evaluate(
            """async ([url, method]) => {
                try {
                    const res = await fetch(url, { method, credentials: 'include' });
                    let body;
                    try { body = await res.json(); } catch (e) { body = await res.text(); }
                    return { status: res.status, ok: res.ok, body };
                } catch (e) {
                    return { status: null, ok: false, body: String(e) };
                }
            }""",
            [url, method],
        )

    return _fetch
