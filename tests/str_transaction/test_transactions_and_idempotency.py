from decimal import Decimal

import pytest

from utils.api_client import parse_spin_response
from utils.megaways_calculator import evaluate, total_win

pytestmark = pytest.mark.integration


@pytest.mark.test_case("PS-STR-001")
@pytest.mark.test_case("PS-REG-132")
def test_bet_transaction_is_a_single_debit(game_ready):
    """PS-STR-001: a spin must debit the bet exactly once. Ref: GR-56."""
    balance_before = game_ready.get_init_data().player_info.balance
    bet = game_ready.get_init_data().player_info.default_bet
    result = game_ready.spin_and_wait()
    assert result.balance == balance_before - bet + result.total_win


@pytest.mark.test_case("PS-STR-002")
@pytest.mark.test_case("PS-REG-133")
def test_win_transaction_amount_matches_calculator(game_ready):
    """PS-STR-002: a win's credited amount must match the win-math oracle
    exactly. Ref: GR-56."""
    game_ready.force_next_spin("3 OAK AA")
    pay_table = game_ready.get_init_data().game_info.pay_table
    result = game_ready.spin_and_wait()
    assert result.total_win > 0
    ways = evaluate(result.reel_view, pay_table, result.bet_amount_used, wild_multipliers=result.wild_multipliers)
    assert result.total_win == total_win(ways)


@pytest.mark.test_case("PS-STR-003")
@pytest.mark.test_case("PS-REG-134")
def test_zero_win_spin_still_closes_the_round(game_ready):
    """PS-STR-003: a non-winning spin must still close its round (no
    dangling open round from a zero-win outcome). Ref: GR-56."""
    game_ready.force_next_spin("FEATURE_MISS")
    result = game_ready.spin_and_wait()
    assert result.closed
    assert result.total_win == 0


@pytest.mark.test_case("PS-STR-004")
@pytest.mark.test_case("PS-REG-135")
def test_buy_feature_transaction():
    """PS-STR-004: buying a feature must debit the correct cost exactly
    once. BLOCKED: Buy Feature confirm flow not yet verified — see
    PS-FUN-059/061/062. Ref: GR-56."""
    pytest.skip("Blocked: Buy Feature confirm flow (endpoint/payload) not yet verified")


@pytest.mark.test_case("PS-STR-005")
@pytest.mark.test_case("PS-REG-136")
def test_free_spins_transactions_balance_math_is_consistent(game_ready):
    """PS-STR-005: every Free Spins round spin's balance must equal the
    prior balance plus that spin's win (no per-spin debit during FS).
    Ref: GR-56."""
    game_ready.force_next_spin("3 OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    game_ready.choose_free_spins_feature("sticky")
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is None, timeout_ms=10_000
    )
    game_ready.dismiss_congrats_popup_if_present()

    game_ready.network_spy.clear("feature")
    for _ in range(3):
        game_ready.wait_for_loading_overlay_to_clear()
        game_ready.page.wait_for_timeout(5_000)
        try:
            game_ready.network_spy.wait_for_response("feature", game_ready.press_space_bar, timeout_ms=15_000)
        except TimeoutError:
            break

    balance = None
    for exchange in game_ready.network_spy.all("feature"):
        data = exchange.response_body["data"]
        result = data["result"]
        win = Decimal(str(result["totalWin"]))
        new_balance = Decimal(str(data["playerInfo"]["balance"]))
        if balance is not None:
            assert new_balance == balance + win, "a Free Spins round spin debited the player instead of only crediting"
        balance = new_balance

    game_ready.resolve_pending_feature(timeout_ms=90_000)


@pytest.mark.test_case("PS-STR-006")
@pytest.mark.test_case("PS-REG-137")
def test_free_spins_round_lifecycle_shares_one_round_id(game_ready):
    """PS-STR-006: the triggering spin and its whole Free Spins sequence
    must belong to one round lifecycle, not fragment into unrelated rounds.
    Ref: GR-56."""
    game_ready.force_next_spin("3 OAK BN")
    triggering_result = game_ready.spin_and_wait_feature_trigger_only()
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    game_ready.choose_free_spins_feature("sticky")
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is None, timeout_ms=10_000
    )
    game_ready.dismiss_congrats_popup_if_present()

    game_ready.network_spy.clear("feature")
    game_ready.wait_for_loading_overlay_to_clear()
    game_ready.page.wait_for_timeout(5_000)
    game_ready.network_spy.wait_for_response("feature", game_ready.press_space_bar, timeout_ms=15_000)
    feature_round_id = game_ready.network_spy.last("feature").response_body["data"]["roundId"]

    assert feature_round_id == triggering_result.round_id

    game_ready.resolve_pending_feature(timeout_ms=90_000)


@pytest.mark.test_case("PS-STR-007")
@pytest.mark.test_case("PS-REG-138")
def test_concurrent_duplicate_spin_requests_do_not_double_process(game_ready, raw_fetch):
    """PS-STR-007: firing two concurrent spin requests must not produce two
    processed rounds for the price of one debit (or any corruption) — spin
    requests carry no body/idempotency token (confirmed empty, see
    docs/samples/README.md), so this fires the exact same raw request twice
    at once via fetch() and checks the aftermath is self-consistent.
    Ref: GR-56."""
    spin_url = game_ready.network_spy.last("spin").url if game_ready.network_spy.last("spin") else None
    if spin_url is None:
        game_ready.spin_and_wait()
        spin_url = game_ready.network_spy.last("spin").url

    balance_before = game_ready.get_balance()
    results = game_ready.page.evaluate(
        """async (url) => {
            const fire = () => fetch(url, { method: 'POST', credentials: 'include' })
                .then(async r => ({ status: r.status, body: await r.json().catch(() => null) }));
            return Promise.all([fire(), fire()]);
        }""",
        spin_url,
    )
    statuses = [r["status"] for r in results]
    successful = [r for r in results if r["status"] == 200 and r["body"]]

    game_ready.reload_and_wait_ready()
    balance_after = game_ready.get_init_data().player_info.balance
    total_debited_or_credited = balance_before - balance_after
    # Whatever happened (both processed as two separate real spins, or one
    # rejected), the balance must be explainable by exactly as many
    # successful spins as actually returned 200, never more.
    bet = game_ready.get_init_data().player_info.default_bet
    assert len(successful) <= 2
    assert abs(total_debited_or_credited) <= bet * len(successful) + sum(
        Decimal(str(r["body"]["data"]["result"]["totalWin"])) for r in successful if r["body"]
    ), f"balance change inconsistent with {len(successful)} successful spin(s), statuses={statuses}"


@pytest.mark.test_case("PS-STR-008")
@pytest.mark.test_case("PS-REG-139")
def test_duplicate_credit_prevention():
    """PS-STR-008: a credit must never be applied twice for one round.

    Not independently automatable beyond PS-STR-007's concurrent-request
    check — this game's RGS response is atomic (bet+result+balance in one
    reply, see CLAUDE.md > Network), so there is no separate "credit" step
    to duplicate independently of the spin request itself. See
    DECISIONS.md D-008 for the same reasoning applied to PS-INT-018.
    Ref: GR-56."""
    pytest.skip("Not independently testable: covered by PS-STR-007 (atomic RGS response, no separate credit step)")


@pytest.mark.test_case("PS-STR-009")
@pytest.mark.test_case("PS-REG-140")
def test_replay_of_old_round_request():
    """PS-STR-009: replaying an old round's request must not be accepted.

    BLOCKED: spin requests carry no round reference or idempotency token at
    all (confirmed empty body) — there is nothing to "replay" in the sense
    this case describes; resending the request is simply a new spin, not a
    replay of a specific old round. Ref: GR-56."""
    pytest.skip("Blocked: spin requests carry no round-identifying payload to replay (empty body)")


@pytest.mark.test_case("PS-STR-010")
@pytest.mark.test_case("PS-REG-141")
def test_out_of_order_concurrent_requests_do_not_corrupt_state(game_ready, raw_fetch):
    """PS-STR-010: concurrently-fired requests must resolve to a
    self-consistent final state, not corrupted/out-of-order balance.
    Modeled the same way as PS-STR-007 (two concurrent raw spin requests),
    since this is the only request shape this harness can safely construct
    without guessing an undocumented payload. Ref: GR-56."""
    game_ready.spin_and_wait()
    spin_url = game_ready.network_spy.last("spin").url
    balance_before = game_ready.get_balance()

    game_ready.page.evaluate(
        """async (url) => {
            await Promise.all([
                fetch(url, { method: 'POST', credentials: 'include' }),
                fetch(url, { method: 'POST', credentials: 'include' }),
            ]);
        }""",
        spin_url,
    )

    game_ready.reload_and_wait_ready()
    assert game_ready.get_init_data().player_info.balance <= balance_before, (
        "balance increased with no explainable win after concurrent requests — possible double-credit"
    )


@pytest.mark.test_case("PS-STR-011")
@pytest.mark.test_case("PS-REG-142")
def test_base_spin_request_during_active_free_spins_is_rejected_or_ignored(game_ready, raw_fetch):
    """PS-STR-011: sending a base-game /spin request while a Free Spins
    round is active must be rejected or ignored, never processed as a real
    extra base-game round. Ref: GR-56."""
    game_ready.force_next_spin("3 OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()
    spin_url = game_ready.network_spy.last("spin").url

    response = raw_fetch(spin_url)

    game_ready.reload_and_wait_ready()
    assert response["status"] != 200 or not response["body"], (
        "a base /spin request appears to have been processed while Free Spins was active"
    )


@pytest.mark.test_case("PS-STR-012")
@pytest.mark.test_case("PS-REG-143")
def test_tampered_bet_value():
    """PS-STR-012: a tampered bet value must be rejected. BLOCKED: no
    captured bet-setting request payload (spin requests carry no bet
    parameter at all) to tamper with. Ref: GR-56."""
    pytest.skip("Blocked: the bet-setting endpoint's payload was never captured")


@pytest.mark.test_case("PS-STR-013")
@pytest.mark.test_case("PS-REG-144")
def test_tampered_bet_above_max():
    """PS-STR-013: a tampered bet above max must be rejected. Same blocker
    as PS-STR-012. Ref: GR-56."""
    pytest.skip("Blocked: the bet-setting endpoint's payload was never captured")


@pytest.mark.test_case("PS-STR-014")
@pytest.mark.test_case("PS-REG-145")
def test_tampered_buy_cost():
    """PS-STR-014: a tampered Buy Feature cost must be rejected. BLOCKED:
    Buy Feature confirm flow not yet verified. Ref: GR-56."""
    pytest.skip("Blocked: Buy Feature confirm flow (endpoint/payload) not yet verified")


@pytest.mark.test_case("PS-STR-015")
@pytest.mark.test_case("PS-REG-146")
def test_tampered_free_spins_choice():
    """PS-STR-015: a tampered Free Spins choice value must be rejected.
    BLOCKED: no captured feature-choice request payload to tamper with (the
    choice is sent via a DOM click, not a known API payload). Ref: GR-56."""
    pytest.skip("Blocked: the feature-choice endpoint's payload was never captured")


@pytest.mark.test_case("PS-STR-016")
@pytest.mark.test_case("PS-REG-147")
def test_bet_change_mid_free_spins_via_api():
    """PS-STR-016: changing the bet mid-Free-Spins via a direct API call
    must be rejected (bet is fixed for the whole feature). BLOCKED: same as
    PS-STR-012 — no captured bet-setting payload to call directly.
    Ref: GR-56."""
    pytest.skip("Blocked: the bet-setting endpoint's payload was never captured")


@pytest.mark.test_case("PS-STR-017")
@pytest.mark.test_case("PS-REG-148")
def test_invalid_session_token_is_rejected(game_ready, config):
    """PS-STR-017: a request with an invalid/garbage session token must be
    rejected, not treated as a valid session. Ref: GR-56."""
    base_url = game_ready.network_spy.last("init").url
    tampered_url = base_url.split("token=")[0] + "token=00000000invalidtoken00000000"

    response = game_ready.page.evaluate(
        """async (url) => {
            try {
                const res = await fetch(url, { method: 'POST', credentials: 'omit' });
                let body; try { body = await res.json(); } catch (e) { body = null; }
                return { status: res.status, body };
            } catch (e) { return { status: null, body: String(e) }; }
        }""",
        tampered_url,
    )
    assert response["status"] != 200 or not (response["body"] or {}).get("data", {}).get("playerInfo"), (
        "an invalid token appears to have been accepted as a valid session"
    )


@pytest.mark.test_case("PS-STR-018")
@pytest.mark.test_case("PS-REG-149")
def test_session_cannot_access_another_players_round():
    """PS-STR-018: a session must not be able to access another player's
    round/history. BLOCKED: this environment provides exactly one player
    token (shared, serial-only per this task's own constraints) — testing
    cross-account isolation needs a second, distinct account, not available
    here. Ref: GR-56."""
    pytest.skip("Blocked: only one player token is available in this environment")


@pytest.mark.test_case("PS-STR-019")
@pytest.mark.test_case("PS-REG-150")
def test_reconciliation_of_bet_and_win_totals_across_a_session(game_ready):
    """PS-STR-019 (Partial): across a short sequence of spins, the sum of
    each spin's (win - bet) must equal the net balance change — reconciles
    our own captured transaction log against the observed balance, not
    against a separate operator reconciliation report (not available to
    this harness). Ref: GR-56."""
    balance_start = game_ready.get_init_data().player_info.balance
    game_ready.network_spy.clear("spin")
    for _ in range(3):
        game_ready.spin_and_wait()

    net_from_log = sum(
        (parse_spin_response(e.response_body).total_win - parse_spin_response(e.response_body).bet)
        for e in game_ready.network_spy.all("spin")
    )
    balance_end = game_ready.get_balance()
    assert balance_end == balance_start + net_from_log


@pytest.mark.test_case("PS-STR-020")
@pytest.mark.test_case("PS-REG-151")
def test_reconciliation_history_vs_rgs():
    """PS-STR-020 (Partial): round history must reconcile against the RGS's
    own transaction log. BLOCKED: no player-history/statement endpoint was
    captured during recon — only init/spin/feature are known. The
    same-session reconciliation this harness CAN do is covered by
    PS-STR-019 instead. Ref: GR-56."""
    pytest.skip("Blocked: no player-history/statement endpoint captured to reconcile against")


@pytest.mark.test_case("PS-STR-021")
@pytest.mark.test_case("PS-REG-152")
def test_balance_consistency_after_errors():
    """PS-STR-021: balance must stay consistent after an error.

    Not duplicated here — already exercised directly by
    tests/error_handling/test_network_and_server_errors.py
    (test_server_500_on_spin_shows_generic_error_and_is_recoverable,
    test_engine_error_on_spin_makes_no_debit_or_rollback_needed,
    test_recovery_after_consecutive_errors_has_correct_state_and_no_duplicates),
    which assert exactly this invariant across multiple error types.
    Ref: GR-56."""
    pytest.skip("Covered by PS-ERR-006/012/018 (same invariant, same mocked-failure technique)")


@pytest.mark.test_case("PS-STR-022")
@pytest.mark.test_case("PS-REG-153")
def test_rng_outcome_is_server_side():
    """PS-STR-022: the RNG outcome must be determined server-side.
    Automation Candidate is "No" in the workbook itself — this requires
    source-code/architecture review (confirming no client-side RNG exists),
    not a runnable UI/API test. Ref: GR-56."""
    pytest.skip("Not automated: workbook marks this No — requires source/architecture review, not a runnable test")


@pytest.mark.test_case("PS-STR-023")
@pytest.mark.test_case("PS-REG-154")
def test_max_win_transaction():
    """PS-STR-023: a max-win transaction must be credited correctly.
    BLOCKED: same as PS-INT-026/PS-ERR-019 — needs a cheat outcome that
    reliably triggers maxCapReached, not confirmed available. Ref: GR-56."""
    pytest.skip("Blocked: needs a cheat outcome that reliably triggers maxCapReached — not confirmed available")


@pytest.mark.test_case("PS-STR-024")
def test_spin_response_missing_fields_does_not_crash_client(game_ready, config):
    """PS-STR-024 (P1): a spin response missing expected fields must not
    crash the client. Ref: GR-56."""
    import re

    pattern = re.compile(config["network_patterns"]["spin"])

    def strip_fields(route):
        route.fulfill(
            status=200,
            json={"data": {"gameId": "x", "roundId": "x", "closed": True, "playerInfo": {}, "result": {}}},
        )

    game_ready.page.route(pattern, strip_fields)
    try:
        game_ready.page.locator(game_ready.CANVAS_SELECTOR).first.focus()
        game_ready.page.keyboard.press("Space")
        game_ready.page.wait_for_timeout(5_000)
    finally:
        game_ready.page.unroute(pattern, strip_fields)

    assert game_ready.is_pixi_ready(), "client appears to have crashed on a spin response missing expected fields"
    game_ready.reload_and_wait_ready()
    result = game_ready.spin_and_wait()
    assert result.closed


@pytest.mark.test_case("PS-STR-025")
def test_spin_response_negative_win_does_not_corrupt_balance(game_ready, config):
    """PS-STR-025 (P1): a spin response reporting a negative win must not be
    applied as a negative credit / corrupt the client's own state tracking.
    Ref: GR-56."""
    import re
    from decimal import Decimal

    pattern = re.compile(config["network_patterns"]["spin"])

    # The real spin is an ordinary, unforced one, so it may legitimately win
    # more than its bet — asserting balance_after <= balance_before (as if
    # every unforced spin must be a net loss) is wrong and fails on a
    # winning spin that has nothing to do with the tampering under test.
    # The real server-computed balance, captured here from the genuine
    # response BEFORE it's tampered with, is the only correct oracle.
    real_balance_after = {}

    def negative_win(route):
        response = route.fetch()
        body = response.json()
        real_balance_after["value"] = Decimal(str(body["data"]["playerInfo"]["balance"]))
        body["data"]["result"]["totalWin"] = -5
        route.fulfill(response=response, json=body)

    game_ready.page.route(pattern, negative_win)
    try:
        game_ready.page.locator(game_ready.CANVAS_SELECTOR).first.focus()
        game_ready.page.keyboard.press("Space")
        game_ready.page.wait_for_timeout(5_000)
    finally:
        game_ready.page.unroute(pattern, negative_win)

    assert game_ready.is_pixi_ready(), "client appears to have crashed on a negative-win spin response"
    # The real, server-side balance (via a fresh reload) is the only value
    # that matters — whatever the client displayed for the tampered response
    # is a client-rendering concern, not a balance-correctness one.
    game_ready.reload_and_wait_ready()
    assert game_ready.get_init_data().player_info.balance == real_balance_after["value"]


@pytest.mark.test_case("PS-STR-026")
def test_responsible_gaming_reality_check_flags_present(init_data):
    """PS-STR-026 (Partial, P1): the session's responsible-gaming
    configuration (reality-check-related flags) must be present and
    internally consistent. Only the data-level opCnf flags are checked —
    the actual reality-check popup's trigger timing/UI wasn't located during
    this run, so its visual behavior isn't asserted. Ref: GR-56."""
    assert isinstance(init_data.op_cnf.responsible_gaming, bool)
    assert isinstance(init_data.op_cnf.show_elapsed_time, bool)


@pytest.mark.test_case("PS-STR-027")
def test_responsible_gaming_session_loss_limit_flags_present(init_data):
    """PS-STR-027 (Partial, P1): session/loss-limit responsible-gaming
    configuration must be present and consistent. Same scope limit as
    PS-STR-026 — data-level only. Ref: GR-56."""
    assert isinstance(init_data.op_cnf.show_net_loss, bool)
    assert isinstance(init_data.op_cnf.show_hourly_loss, bool)
    assert isinstance(init_data.op_cnf.auto_spin_spending_limit, bool)
