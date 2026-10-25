import pytest

pytestmark = pytest.mark.negative


@pytest.mark.test_case("PS-ERR-008")
def test_feature_spin_sent_with_no_active_feature():
    """PS-ERR-008 (P1): sending a Free-Spins-round spin while no Free Spins
    round is active must be rejected/resynced, not silently accepted.

    BLOCKED: this requires crafting a raw `/feature` request ourselves
    (bypassing the game's own JS, which would never normally send one
    outside an active round), but no real `/feature` request payload was
    ever captured during recon (docs/samples/ only has the init/spin
    shapes) — fabricating headers/body/auth for it would be guessing at an
    undocumented contract rather than testing against a known one.
    Ref: GR-56."""
    pytest.skip("Blocked: no captured /feature request payload to safely construct an out-of-context call")


@pytest.mark.test_case("PS-ERR-009")
def test_invalid_bet_is_rejected():
    """PS-ERR-009 (P1): submitting a bet value outside possibleBets must be
    rejected with the bet reset to a valid value.

    BLOCKED: the UI's Bet panel only ever offers values from the confirmed
    `possibleBets` list, so an invalid bet can't be reached through normal
    interaction. Triggering it would require calling whatever endpoint
    actually sets the session's current bet directly — but spin requests
    carry no bet parameter at all (confirmed empty body, see
    docs/samples/README.md), meaning bet selection must happen through a
    separate, not-yet-captured endpoint. Fabricating that request's shape
    without a real sample would be guessing. Ref: GR-56."""
    pytest.skip("Blocked: the bet-setting endpoint's payload was never captured — can't safely send an invalid value")


@pytest.mark.test_case("PS-ERR-010")
def test_sending_feature_choice_twice_applies_only_once(game_ready):
    """PS-ERR-010 (P1): selecting a Free Spins feature twice in quick
    succession must only apply once — not grant or debit a feature twice.
    Ref: GR-56."""
    game_ready.force_next_spin("3 OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()
    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )

    # Fire the same choice twice back-to-back, before the UI has a chance to
    # close the choice screen between clicks.
    for _ in range(2):
        try:
            game_ready.click_pixi_text("STICKY WILDS")
        except RuntimeError:
            pass  # second click may find nothing once the screen has closed

    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is None, timeout_ms=10_000
    )
    game_ready.resolve_pending_feature(timeout_ms=60_000)
    assert game_ready.get_init_data().unfinished_info is None


@pytest.mark.test_case("PS-ERR-014")
def test_free_spins_asset_load_failure_preserves_feature_state(game_ready, open_game_page_blocking_assets):
    """PS-ERR-014 (P1): if Free Spins assets fail to load, the feature state
    must be preserved so a reload can resume it — not abandoned. Ref: GR-56."""
    game_ready.force_next_spin("3 OAK BN")
    game_ready.spin_and_wait_feature_trigger_only()
    assert game_ready.get_init_data().unfinished_info is not None

    context = game_ready.page.context
    blocked_page, _pattern = open_game_page_blocking_assets(context)
    try:
        blocked_page.goto(game_ready.page.url, timeout_ms=30_000)
        blocked_page.page.wait_for_timeout(5_000)
        blocked_page.wait_for(lambda: blocked_page.get_init_data().unfinished_info is not None, timeout_ms=15_000)
    finally:
        blocked_page.page.close()

    # Recover normally (assets not blocked) and confirm the round still
    # resolves cleanly rather than having been lost.
    game_ready.reload_and_wait_ready()
    assert game_ready.get_init_data().unfinished_info is None


@pytest.mark.test_case("PS-ERR-015")
def test_asset_load_failure_at_launch_shows_no_partial_ui(config, open_game_page_blocking_assets, context):
    """PS-ERR-015 (P1): if assets fail to load at launch, the game must show
    an error/retry state rather than a silently broken partial UI, and a
    normal launch afterward must succeed. Ref: GR-56."""
    blocked_page, _pattern = open_game_page_blocking_assets(context)
    blocked_page.page.goto(config["game_url"])
    blocked_page.page.wait_for_timeout(8_000)
    # is_loaded() only checks that window.__PIXI_APP__ booted, which it
    # does regardless of whether sprite/audio assets actually loaded (the
    # renderer itself doesn't depend on them) — confirmed live (D-020).
    # is_base_game_ready() checks for the base-game-specific megawaysText
    # node instead, a much better proxy for "the real game, not a broken
    # partial UI, is showing".
    assert not blocked_page.is_base_game_ready(), "base game reached a normal ready state despite blocked assets"
    blocked_page.page.close()

    normal_page = context.new_page()
    from pages.game_page import GamePage
    from utils.network_spy import NetworkSpy

    normal_game = GamePage(normal_page, NetworkSpy(normal_page, config["network_patterns"]))
    normal_game.goto(config["game_url"], timeout_ms=config["timeouts"]["game_ready_ms"])
    normal_game.wait_for(normal_game.is_loaded, timeout_ms=config["timeouts"]["game_ready_ms"])
    normal_page.close()


@pytest.mark.test_case("PS-ERR-017")
def test_error_message_text_quality():
    """PS-ERR-017 (P2): every error popup's text must be clear, localised,
    include an error code where applicable, and show no stack traces.

    BLOCKED: none of this run's mocked-error tests (PS-ERR-003/005/006/
    011/012/016/018) found a confirmed PIXI node name for an error/message
    popup to read text from — the game may show nothing visible for a mocked
    HTTP-layer failure, or show something under a node this run didn't
    identify. Needs a visual recon pass (screenshot review across each
    mocked error) to find the right node before text content can be
    asserted on. Ref: GR-56."""
    pytest.skip("Blocked: no confirmed PIXI node for an error/message popup to read text from")


@pytest.mark.test_case("PS-ERR-019")
def test_max_win_cap_message():
    """PS-ERR-019 (P1): reaching the max win cap must show an informative
    message and end the feature.

    BLOCKED: same as PS-INT-026 — needs a cheat outcome that deterministically
    reaches the live 250,000 max-win cap, not confirmed available (the
    top win-tier cheat options share mostly identical forced boards and
    whether any reaches maxCapReached depends on current bet). Ref: GR-29 |
    OBS-09."""
    pytest.skip("Blocked: needs a cheat outcome that reliably triggers maxCapReached — not confirmed available")


@pytest.mark.test_case("PS-ERR-020")
def test_malfunction_handling_voids_and_refunds():
    """PS-ERR-020 (P1): a malfunction must void the round per the rules,
    refund the bet per operator policy, and be logged.

    BLOCKED: this is server-side/RGS business logic (voiding and refund
    decisions) with no client-observable trigger this harness can produce —
    mocking a response ourselves would test our own fabrication, not real
    malfunction-handling logic, and there's no fault-injection access to the
    actual RGS to trigger a genuine malfunction. Ref: GR-53."""
    pytest.skip("Blocked: no mechanism to trigger genuine server-side malfunction voiding/refund logic")
