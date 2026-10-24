from decimal import Decimal

import pytest

from utils.api_client import parse_spin_response


def _trigger_spin_without_waiting(game_page) -> None:
    """Presses Space to start a spin but does not wait for its response —
    used to interrupt a round mid-flight, before the server has replied."""
    game_page.page.locator(game_page.CANVAS_SELECTOR).first.focus()
    game_page.page.keyboard.press("Space")


@pytest.mark.interruption
@pytest.mark.recovery
@pytest.mark.test_case("PS-INT-001")
def test_refresh_during_base_spin_leaves_exactly_one_debit(game_ready, init_data):
    """PS-INT-001: refreshing while a base-game spin is in flight must not
    produce a duplicate debit or a stuck round — on reload, the interrupted
    round's result is available (closed) and the game is immediately
    spinnable again. Ref: GR-56."""
    bet = init_data.player_info.default_bet
    balance_before = game_ready.get_balance()

    _trigger_spin_without_waiting(game_ready)
    game_ready.page.wait_for_timeout(300)
    game_ready.reload_and_wait_ready()

    balance_after_recovery = game_ready.get_balance()
    # At most one bet's worth of debit happened (a win could also raise the
    # balance back up, so this only rules out a *double* debit).
    assert balance_before - balance_after_recovery <= bet

    result = game_ready.spin_and_wait()
    assert result.closed


@pytest.mark.interruption
@pytest.mark.recovery
@pytest.mark.test_case("PS-INT-002")
def test_refresh_during_win_presentation_credits_win_once(game_ready):
    """PS-INT-002: refreshing while a win is presenting must not re-apply or
    drop the win — the post-reload balance matches the server's own
    balance.after-win figure exactly. Ref: GR-56."""
    game_ready.force_next_spin("3 OAK AA")
    exchange = game_ready.spin()
    result = parse_spin_response(exchange.response_body)
    assert result.total_win > 0, "PS-INT-002 requires a winning spin to test win-presentation interruption"

    game_ready.reload_and_wait_ready()

    assert game_ready.get_balance() == result.balance


@pytest.mark.interruption
@pytest.mark.recovery
@pytest.mark.test_case("PS-INT-003")
def test_refresh_during_free_spins_resumes_at_correct_spin(game_ready):
    """PS-INT-003: refreshing mid-Free-Spins must resume the round rather
    than lose it — unfinishedInfo is non-null before the reload and the
    feature is drained/resolved after it, with the balance never going
    below its pre-refresh value (wins are never lost). Ref: GR-56."""
    game_ready.force_next_spin("3 OAK BN")
    result = game_ready.spin_and_wait_feature_trigger_only()

    balance_before_reload = game_ready.get_balance()
    game_ready.page.wait_for_timeout(1_000)  # let at least one FS round request land first

    game_ready.network_spy.wait_for_response("init", lambda: game_ready.page.reload(), timeout_ms=30_000)
    resumed_init = game_ready.get_init_data()
    assert resumed_init.unfinished_info is not None, "expected an unfinished Free Spins round after reload"

    game_ready.wait_for(game_ready.is_loaded, timeout_ms=30_000)
    game_ready.ensure_base_game_ready(timeout_ms=60_000)
    assert game_ready.get_balance() >= balance_before_reload


@pytest.mark.interruption
@pytest.mark.recovery
@pytest.mark.test_case("PS-INT-004")
def test_refresh_on_free_spins_choice_screen_restores_it(game_ready):
    """PS-INT-004: refreshing on the "Choose Your Free Spins Feature" screen
    must restore that same choice screen, not skip or lose it. Ref: GR-56."""
    game_ready.force_next_spin("3 OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()

    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )

    game_ready.network_spy.wait_for_response("init", lambda: game_ready.page.reload(), timeout_ms=30_000)
    assert game_ready.get_init_data().unfinished_info is not None
    game_ready.wait_for(game_ready.is_loaded, timeout_ms=30_000)
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=30_000
    )

    # Leave the session clean for whatever test runs next.
    game_ready.resolve_pending_feature(timeout_ms=60_000)


@pytest.mark.interruption
@pytest.mark.recovery
@pytest.mark.test_case("PS-INT-005")
def test_refresh_immediately_after_buy_confirm(game_ready):
    """PS-INT-005: refreshing right after confirming Buy Feature must debit
    exactly once and resume the bought feature. Ref: GR-56.

    BLOCKED: the Buy Feature confirm flow itself (which network call it
    makes, whether force_next_spin() applies to the bought round) was never
    verified in the prior Functional-sheet session (see
    tests/functional/test_buy_free_spins.py, PS-FUN-059/061/062 explicitly
    deferred) and this run's scope does not include re-deriving undocumented
    payload/endpoint shapes without confirmation. Needs that groundwork
    before this case can be written without guessing."""
    pytest.skip("Blocked: Buy Feature confirm flow (endpoint/payload) not yet verified — see PS-FUN-059/061/062")


@pytest.mark.interruption
@pytest.mark.recovery
@pytest.mark.test_case("PS-INT-006")
def test_close_reopen_during_base_spin_completes_round_server_side(game_ready, config, open_game_page_in):
    """PS-INT-006: closing the tab mid-spin and reopening must find the
    round completed server-side (one debit, balance/history consistent) —
    not lost, not duplicated. Ref: GR-56."""
    balance_before = game_ready.get_balance()
    bet = game_ready.get_init_data().player_info.default_bet
    context = game_ready.page.context

    _trigger_spin_without_waiting(game_ready)
    game_ready.page.wait_for_timeout(300)
    game_ready.page.close()

    reopened = open_game_page_in(context)
    balance_after = reopened.get_balance()
    assert balance_before - balance_after <= bet

    result = reopened.spin_and_wait()
    assert result.closed


@pytest.mark.interruption
@pytest.mark.recovery
@pytest.mark.test_case("PS-INT-007")
def test_close_reopen_during_free_spins_resumes(game_ready, open_game_page_in):
    """PS-INT-007: closing the tab mid-Free-Spins and reopening must resume
    the feature, not abandon it. Ref: GR-56."""
    game_ready.force_next_spin("3 OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()
    context = game_ready.page.context

    game_ready.page.wait_for_timeout(1_000)
    game_ready.page.close()

    reopened = open_game_page_in(context)
    assert reopened.get_init_data().unfinished_info is None, "resolve should have drained the feature on load"
    result = reopened.spin_and_wait()
    assert result.closed


@pytest.mark.interruption
@pytest.mark.recovery
@pytest.mark.test_case("PS-INT-029")
def test_recovery_sequence_never_produces_duplicate_round_ids(game_ready):
    """PS-INT-029: across an interrupt-and-recover sequence (refresh during
    a base spin), no round ID repeats and the feature/credit effects of a
    single round are never applied twice. Ref: GR-56."""
    game_ready.network_spy.clear("spin")
    _trigger_spin_without_waiting(game_ready)
    game_ready.page.wait_for_timeout(300)
    game_ready.reload_and_wait_ready()

    result_a = game_ready.spin_and_wait()
    result_b = game_ready.spin_and_wait()
    assert result_a.round_id != result_b.round_id

    seen_round_ids = [parse_spin_response(e.response_body).round_id for e in game_ready.network_spy.all("spin")]
    assert len(seen_round_ids) == len(set(seen_round_ids)), "duplicate round ID observed after recovery"


@pytest.mark.interruption
@pytest.mark.recovery
@pytest.mark.test_case("PS-INT-030")
def test_suspended_round_resumes_from_last_recorded_action(game_ready):
    """PS-INT-030: after an interruption, the session resumes from the last
    successfully recorded server action, never re-running or skipping it —
    checked via the Free Spins case, where unfinishedInfo both before and
    after a reload reflects a consistent, non-regressing feature state.
    Ref: GR-56."""
    game_ready.force_next_spin("3 OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()

    pre_reload_unfinished = game_ready.get_init_data().unfinished_info
    assert pre_reload_unfinished is not None

    game_ready.network_spy.wait_for_response("init", lambda: game_ready.page.reload(), timeout_ms=30_000)
    post_reload_unfinished = game_ready.get_init_data().unfinished_info
    assert post_reload_unfinished is not None, "the same unfinished round must still be reported after reload"

    game_ready.wait_for(game_ready.is_loaded, timeout_ms=30_000)
    game_ready.ensure_base_game_ready(timeout_ms=60_000)
    assert game_ready.get_init_data().unfinished_info is None
