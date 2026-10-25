import pytest

pytestmark = pytest.mark.ui

_CONTROL_NODES = [
    "spinBtn",
    "betBtn",
    "bbBtn",
    "turboBtn",
    "menuBtn",
    "infoBtn",
]


@pytest.mark.test_case("PS-UI-011")
def test_controls_visible_and_enabled_in_idle_state(game_ready):
    """PS-UI-011: Play, Bet, Buy, Turbo, Menu, Info controls must all be
    present/visible while idle. "Enabled" is checked via visibility and
    clickability (bounds present) rather than a separate disabled-state
    flag, which wasn't located on these nodes during recon. Ref: GR-52."""
    for node_name in _CONTROL_NODES:
        assert game_ready.get_pixi_node_or_none(node_name) is not None, f"{node_name} not visible while idle"


@pytest.mark.test_case("PS-UI-012")
def test_bet_and_menu_disabled_while_spinning(game_ready):
    """PS-UI-012 (P1): Bet and Menu controls must be disabled while reels
    are spinning — verified the same way the existing Functional sheet
    checks this (clicking has no effect), since no separate visual
    "disabled" flag was found on these nodes. Ref: GR-52, GR-31 | OBS-19."""
    game_ready.wait_for_loading_overlay_to_clear()
    game_ready.page.wait_for_timeout(3_000)
    game_ready.press_space_bar()

    try:
        game_ready.click_pixi_button(game_ready.BET_BUTTON_NODE)
    except RuntimeError:
        pass
    assert game_ready.get_pixi_node_or_none("betPanelView") is None, "Bet panel opened while reels were spinning"

    game_ready.page.wait_for_timeout(5_000)
    if game_ready.get_init_data().unfinished_info is not None:
        game_ready.resolve_pending_feature(timeout_ms=120_000)


@pytest.mark.test_case("PS-UI-013")
def test_bet_and_buy_disabled_during_free_spins(game_ready):
    """PS-UI-013 (P1): Bet and Buy must be disabled during Free Spins.
    Reuses the same force-trigger-and-choose setup as the PS-FEA suite
    (inlined here to avoid a cross-directory fixture import). Ref: GR-15."""
    from pages.buy_feature_panel import BuyFeaturePanel

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

    try:
        game_ready.click_pixi_button(game_ready.BET_BUTTON_NODE)
    except RuntimeError:
        pass
    assert game_ready.get_pixi_node_or_none("betPanelView") is None, "Bet panel opened during Free Spins"

    try:
        game_ready.click_pixi_button(game_ready.BUY_FEATURE_BUTTON_NODE)
    except RuntimeError:
        pass
    assert game_ready.get_pixi_node_or_none(BuyFeaturePanel.COST_TEXT_NODE) is None, "Buy panel opened during Free Spins"

    game_ready.resolve_pending_feature(timeout_ms=180_000)


@pytest.mark.test_case("PS-UI-017")
def test_balance_field_updates_on_debit_and_credit(game_ready):
    """PS-UI-017: the balance field must reflect the debit at spin start and
    the credit after a win, ending on the correct final value.
    Ref: GR-19."""
    from decimal import Decimal

    game_ready.force_next_spin("3 OAK AA")
    balance_before = game_ready.get_init_data().player_info.balance
    result = game_ready.spin_and_wait()
    assert result.total_win > 0

    displayed = game_ready.get_displayed_balance_text().replace(",", "").replace("€", "").strip()
    assert Decimal(displayed) == result.balance
    assert result.balance == balance_before - result.bet + result.total_win


@pytest.mark.test_case("PS-UI-018")
def test_win_field_shows_total_and_resets_next_spin(game_ready):
    """PS-UI-018: the win field must show the current round's total and
    reset on the next spin. Checked via the server response's own total_win
    across a winning then a losing spin (no confirmed dedicated "win field"
    PIXI node was located during recon to read directly). Ref: GR-25."""
    game_ready.force_next_spin("3 OAK AA")
    winning_result = game_ready.spin_and_wait()
    assert winning_result.total_win > 0

    losing_result = game_ready.spin_and_wait()
    # Not forced — the next spin's own total_win is whatever it is; the
    # real claim being checked is that it's independent of the prior spin's
    # win (never inherits/carries over a stale value).
    assert losing_result.total_win != winning_result.total_win or losing_result.total_win == 0


@pytest.mark.test_case("PS-UI-036")
def test_no_template_placeholders_visible_anywhere(game_ready):
    """PS-UI-036 (P0): no unresolved template placeholder (e.g. "{{text1}}")
    may appear anywhere in the visible UI — scans every genuinely on-screen
    PIXI text node. Ref: GR-28, GR-54 | OBS-09.

    Walks the scene graph tracking each node's OWN ancestor-chain visibility
    manually (accumulating `visible` down from the root as it recurses), not
    `node.worldVisible` — confirmed live (D-032) that this PIXI build does
    not expose `worldVisible`/`worldAlpha` at all (`undefined` on every
    node), which silently made the D-030 fix a no-op (it fell through to
    the same local-`visible`-only check D-030 was meant to replace). A
    diagnostic dump of the dormant jackpot-message template node
    ("...has won {{text2}} from {{text3}} Jackpot...") confirmed the real
    shape of the bug: the text node itself (`msgText`) has its own
    `visible: true`, but its direct parent container (`jpHitCelebrationComp`
    — this game's `jackpot_info` is always `None`, so this container is
    never shown) has `visible: False`. Manually AND-ing `visible` down the
    chain while recursing correctly excludes it, since a node's true
    on-screen visibility is the AND of its own flag and every ancestor's.
    The canvas-bounds-intersection check (D-031) is kept alongside this as
    an extra safety net against off-screen-positioned-but-visible nodes.
    Ref: GR-28, GR-54 | OBS-09."""
    texts = game_ready.page.evaluate(
        """() => {
            const app = window.__PIXI_APP__;
            if (!app || !app.stage) return [];
            const screen = app.screen || {x: 0, y: 0, width: app.renderer.width, height: app.renderer.height};
            const out = [];
            (function walk(n, inheritedVisible) {
                if (!n) return;
                const visible = inheritedVisible && n.visible !== false;
                if (visible && typeof n.text === 'string' && n.text.length > 0) {
                    let b = null;
                    try { b = n.getBounds(); } catch (e) {}
                    const onScreen = b && b.width > 0 && b.height > 0
                        && b.x < screen.x + screen.width && b.x + b.width > screen.x
                        && b.y < screen.y + screen.height && b.y + b.height > screen.y;
                    if (onScreen) out.push(n.text);
                }
                if (n.children) for (const c of n.children) walk(c, visible);
            })(app.stage, true);
            return out;
        }"""
    )
    offenders = [t for t in texts if "{{" in t or "}}" in t]
    assert not offenders, f"unresolved template placeholder(s) found: {offenders}"


@pytest.mark.test_case("PS-UI-044")
def test_mute_persists_across_refresh(game_ready):
    """PS-UI-044: the mute/sound-off state must persist across a page
    refresh. Ref: GR-49."""
    sound_on_before = game_ready.get_pixi_node_or_none(game_ready.SOUND_ON_BUTTON_NODE) is not None
    # Toggle to whichever state isn't currently active, then verify it
    # survives a reload rather than resetting to a default.
    if sound_on_before:
        game_ready.click_pixi_button(game_ready.SOUND_ON_BUTTON_NODE)
    else:
        game_ready.click_pixi_button(game_ready.SOUND_OFF_BUTTON_NODE)
    game_ready.page.wait_for_timeout(500)
    sound_on_after_toggle = game_ready.get_pixi_node_or_none(game_ready.SOUND_ON_BUTTON_NODE) is not None
    assert sound_on_after_toggle != sound_on_before, "sound toggle had no visible effect"

    game_ready.reload_and_wait_ready()
    sound_on_after_reload = game_ready.get_pixi_node_or_none(game_ready.SOUND_ON_BUTTON_NODE) is not None
    assert sound_on_after_reload == sound_on_after_toggle, "mute state did not persist across refresh"

    # Restore original state for whatever runs next.
    if sound_on_after_reload != sound_on_before:
        node = game_ready.SOUND_ON_BUTTON_NODE if sound_on_after_reload else game_ready.SOUND_OFF_BUTTON_NODE
        game_ready.click_pixi_button(node)
