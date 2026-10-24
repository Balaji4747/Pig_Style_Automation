import pytest

pytestmark = pytest.mark.negative


@pytest.mark.test_case("PS-ERR-001")
def test_insufficient_balance_on_spin_makes_no_debit(game_ready, mock_spin_failure):
    """PS-ERR-001: attempting to spin with insufficient balance must show an
    error and make no debit.

    Partial: this session's balance is far too large (see DECISIONS.md
    D-005/D-006 — a prior bug let it run away to ~6.1M EUR) to genuinely
    drain to below one bet in a reasonable number of real spins, so this
    mocks the spin response with a synthetic insufficient-funds status
    (402) instead of a real low-balance condition. SPEC QUESTION: no
    documented real error shape for this case was available to mock
    precisely. Ref: GR-22."""
    balance_before = game_ready.get_init_data().player_info.balance

    def insufficient_funds(route):
        route.fulfill(status=402, json={"error": "INSUFFICIENT_BALANCE"})

    exchange = mock_spin_failure(insufficient_funds)
    assert exchange is not None and exchange.status == 402

    game_ready.reload_and_wait_ready()
    assert game_ready.get_init_data().player_info.balance == balance_before
    result = game_ready.spin_and_wait()
    assert result.closed


@pytest.mark.test_case("PS-ERR-002")
def test_insufficient_balance_on_buy_makes_no_debit():
    """PS-ERR-002: attempting to Buy Feature with insufficient balance must
    show an error and make no debit.

    BLOCKED: the Buy Feature confirm flow's network call was never verified
    (see PS-FUN-059/061/062, PS-INT-005) — mocking its failure mode without
    knowing which endpoint/payload it actually uses would be guessing at two
    unknowns at once. Needs that groundwork first. Ref: GR-36."""
    pytest.skip("Blocked: Buy Feature confirm flow (endpoint/payload) not yet verified — see PS-FUN-059/061/062")


@pytest.mark.test_case("PS-ERR-003")
@pytest.mark.test_case("PS-EDG-030")
def test_session_expired_on_spin_shows_error_and_allows_relaunch(game_ready, mock_spin_failure):
    """PS-ERR-003: a spin attempt with an expired session must show a
    session-expired message and offer a reload/relaunch path.

    SPEC QUESTION: no documented real expired-session response shape was
    available; this mocks a generic 401 and only asserts recoverability via
    reload, not the specific in-session message text/prompt. Ref: GR-56."""
    exchange = mock_spin_failure(lambda route: route.fulfill(status=401, json={"error": "SESSION_EXPIRED"}))
    assert exchange is not None and exchange.status == 401

    game_ready.reload_and_wait_ready()
    result = game_ready.spin_and_wait()
    assert result.closed


@pytest.mark.test_case("PS-ERR-004")
def test_concurrent_login_on_spin_shows_session_invalid(game_ready, mock_spin_failure):
    """PS-ERR-004 (P1): a spin attempt after logging in elsewhere must show
    a session-invalid message.

    SPEC QUESTION: from the client's perspective this is likely
    indistinguishable from PS-ERR-003's expired-session response (both are
    "the server rejected this request as unauthenticated") — mocked here
    with the same generic 401, since no distinct documented shape exists for
    "invalidated by concurrent login" specifically. Only recoverability is
    asserted. Ref: GR-56."""
    exchange = mock_spin_failure(lambda route: route.fulfill(status=401, json={"error": "SESSION_INVALID"}))
    assert exchange is not None and exchange.status == 401

    game_ready.reload_and_wait_ready()
    result = game_ready.spin_and_wait()
    assert result.closed
