from decimal import Decimal

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage
from pages.auto_spin_panel import AutoSpinPanel
from pages.bet_panel import BetPanel
from pages.buy_feature_panel import BuyFeaturePanel
from pages.cheat_panel import CheatPanel
from pages.rules_page import RulesPage
from pages.paytable_page import PaytablePage
from utils.api_client import InitResponse, SpinResult, parse_init_response, parse_spin_response
from utils.canvas_helper import percent_to_pixels
from utils.network_spy import CapturedExchange, NetworkSpy


class GamePage(BasePage):
    """Main game screen. The game is pure canvas (PIXI.js) with zero DOM
    controls, so buttons are clicked via their live PIXI scene-graph node
    name (see BasePage.click_pixi_button), not hardcoded coordinates.
    Balance/bet/win/reels come from the intercepted init/spin API responses
    (via NetworkSpy), parsed into typed Decimal-based dataclasses by
    utils/api_client.py — not from canvas pixels.

    Confirmed endpoints (23 Oct 2026, qa env):
      init: POST https://api.test.spiniq.io/gs/pack-alpha/games/init
      spin: POST https://api.test.spiniq.io/gs/pack-alpha/games/spin
    """

    # "startBtn" is NOT used to dismiss the splash: the game reuses that node
    # name across several popups (splash, feature-intro, etc), so clicking
    # "the first visible startBtn" is ambiguous and was confirmed unreliable
    # in testing. "splashView" is the splash's own container and is a
    # reliable, unambiguous signal of whether it's showing.
    SPLASH_VIEW_NODE = "splashView"
    # PLAY GAME button position as a fraction of canvas size (confirmed
    # reliable across many manual runs; see CLAUDE.md > Locator strategy).
    PLAY_GAME_POSITION_PCT = (50.0, 83.8)
    # Base-game-only UI element (the MEGAWAYS counter). Confirmed to never
    # exist while the splash is showing, unlike spinBtn (see is_loaded's
    # docstring) — used as the "definitely on the base game" signal, since
    # the splash is sometimes skipped by the server entirely (session/
    # preference-dependent) and never appears at all.
    BASE_GAME_READY_NODE = "megawaysText"
    # "CHOOSE YOUR FREE SPINS FEATURE" title and the post-feature
    # "Congratulations" popup — used to auto-recover from any spin that
    # triggers a feature (forced outcomes can trigger one incidentally,
    # e.g. "6 OAK AA" sometimes also lands Bonus symbols).
    FEATURE_CHOICE_TITLE_NODE = "selectionTxt"
    CONGRATS_TEXT_NODE = "congratText"
    # "Please wait, loading feature game assets" overlay — confirmed to
    # block spin input while showing (same stale-visible-flag issue as
    # elsewhere: megawaysText still reports visible=true underneath it, so
    # it must be checked separately, not folded into is_base_game_ready).
    LOADING_OVERLAY_NODE = "loader_anim"

    SPIN_BUTTON_NODE = "spinBtn"
    STOP_SPIN_BUTTON_NODE = "stopSpinBtn"
    STOP_AUTO_BUTTON_NODE = "stopAutoBtn"
    BET_BUTTON_NODE = "betBtn"
    BUY_FEATURE_BUTTON_NODE = "bbBtn"
    MENU_BUTTON_NODE = "menuBtn"
    INFO_BUTTON_NODE = "infoBtn"
    TURBO_BUTTON_NODE = "turboBtn"
    SOUND_ON_BUTTON_NODE = "soundOnBtn"
    SOUND_OFF_BUTTON_NODE = "soundOffBtn"

    def __init__(self, page: Page, network_spy: NetworkSpy):
        super().__init__(page)
        self.network_spy = network_spy

    def goto(self, url: str, timeout_ms: int = 30_000) -> None:
        """Navigates to the game and waits specifically for the init
        response caused by this navigation (via NetworkSpy.wait_for_response
        / Playwright's expect_response), not a poll of "has an init response
        shown up yet"."""
        self.network_spy.wait_for_response("init", lambda: super(GamePage, self).goto(url), timeout_ms=timeout_ms)

    def is_splash_visible(self) -> bool:
        return self.get_pixi_node_or_none(self.SPLASH_VIEW_NODE) is not None

    def is_base_game_ready(self) -> bool:
        return self.get_pixi_node_or_none(self.BASE_GAME_READY_NODE) is not None

    def is_loading_overlay_visible(self) -> bool:
        return self.get_pixi_node_or_none(self.LOADING_OVERLAY_NODE) is not None

    def wait_for_loading_overlay_to_clear(self, timeout_ms: int = 60_000) -> None:
        """The "Please wait, loading feature game assets" overlay can appear
        at any point (observed: after playing a Free Spins round) and blocks
        spin input while showing. Given a generous timeout since it can be
        a real asset download, not just an animation."""
        self.wait_for(lambda: not self.is_loading_overlay_visible(), timeout_ms=timeout_ms)

    def dismiss_splash(self, timeout_ms: int = 30_000) -> None:
        """Click PLAY GAME on the splash screen to reach the base game.

        Loading happens in two stages: a generic platform loader first (no
        PIXI app yet, or an empty stage), then the Pig Style splash itself
        (with a loading bar of its own before PLAY GAME appears). So
        is_splash_visible()==False is ambiguous on its own — it means either
        "dismissed" or "hasn't rendered yet". This first waits for the splash
        to actually appear, then retries clicking until it's gone (a click
        on the loading-bar area does nothing, so a single click can't be
        trusted either)."""
        self.wait_for(self.is_splash_visible, timeout_ms=timeout_ms)

        canvas_box = self.page.locator(self.CANVAS_SELECTOR).first.bounding_box()
        x, y = percent_to_pixels(canvas_box, *self.PLAY_GAME_POSITION_PCT)

        def try_dismiss() -> bool:
            self.click_canvas(x, y)
            return not self.is_splash_visible()

        self.wait_for(try_dismiss, timeout_ms=timeout_ms, interval_ms=500)

    def ensure_base_game_ready(self, timeout_ms: int = 30_000) -> None:
        """Waits until the base game is interactable, dismissing the splash
        screen if one appears. The splash is sometimes skipped entirely
        (server/session-dependent) and the game goes straight to the base
        game once assets finish loading — this handles both cases.

        Also resolves any pending round left over from a previous session
        (e.g. an unresolved Free Spins choice): the init response's
        `unfinishedInfo` is a reliable, immediate signal for this — the
        choice-screen popup itself fades in, so checking for it visually
        right after load is timing-sensitive and was confirmed unreliable."""
        self.wait_for(lambda: self.is_splash_visible() or self.is_base_game_ready(), timeout_ms=timeout_ms)
        if self.is_splash_visible():
            self.dismiss_splash(timeout_ms=timeout_ms)
        self.wait_for(self.is_base_game_ready, timeout_ms=timeout_ms)
        self.wait_for_loading_overlay_to_clear(timeout_ms=timeout_ms)
        self.dismiss_connection_error_if_present()

        # resolve_pending_feature() is itself best-effort (timing-based), so
        # a single pass is not guaranteed to fully drain a round with an
        # unusually long celebration — confirmed live: a round could still
        # be stuck mid-sequence after one resolve attempt. Re-check against
        # a FRESH init response (via reload, not the possibly-stale
        # in-memory one) and retry a bounded number of times rather than
        # trusting one attempt.
        for _ in range(3):
            if self.get_init_data().unfinished_info is None:
                return
            self.resolve_pending_feature(timeout_ms=timeout_ms)
            self.network_spy.wait_for_response("init", lambda: self.page.reload(), timeout_ms=timeout_ms)
            self.wait_for(self.is_loaded, timeout_ms=timeout_ms)
            self.wait_for(self.is_base_game_ready, timeout_ms=timeout_ms)
            self.wait_for_loading_overlay_to_clear(timeout_ms=timeout_ms)

        # Surface a genuinely-unresolvable round loudly and immediately,
        # rather than silently handing back a still-broken session to the
        # caller — confirmed live this let a stuck round cascade into a
        # later, unrelated test's failure instead of this one's, which made
        # the real problem much harder to see (three separate incidents,
        # see DECISIONS.md D-005/D-006/D-009/D-011/D-012).
        if self.get_init_data().unfinished_info is not None:
            raise RuntimeError(
                "ensure_base_game_ready: round still unfinished after 3 resolve-and-reload attempts"
            )

    def is_loaded(self) -> bool:
        """Whether the game's PIXI app has initialized (post goto(), which
        already guarantees the init response arrived)."""
        return self.page.locator(self.CANVAS_SELECTOR).count() > 0 and self.is_pixi_ready()

    def get_init_data(self) -> InitResponse:
        """Parsed init response (paytable, bet limits, currency, rtp, opCnf
        flags, unfinishedInfo, etc.) for the current game session."""
        exchange = self.network_spy.last("init")
        if exchange is None or exchange.response_body is None:
            raise RuntimeError("No init response captured yet — game may not be ready")
        return parse_init_response(exchange.response_body)

    def get_balance(self) -> Decimal:
        spin_exchange = self.network_spy.last("spin")
        if spin_exchange is not None and spin_exchange.response_body is not None:
            return parse_spin_response(spin_exchange.response_body).balance
        return self.get_init_data().player_info.balance

    def spin(self, timeout_ms: int = 10_000) -> CapturedExchange:
        """Triggers a spin and returns the raw captured exchange for the
        response it causes, via NetworkSpy.wait_for_response (tied to this
        specific action, not a poll of "last captured"). Use spin_and_wait()
        for the parsed result.

        Uses the documented Space-bar shortcut ("Press the spin button or
        the space bar to start a game round") rather than clicking the
        spinBtn PIXI node directly: in testing, a simulated click on the
        button's computed bounds did not reliably register with the game's
        event system, while Space was 100% reliable. See CLAUDE.md > Locator
        strategy for details."""
        self.dismiss_connection_error_if_present()
        self.wait_for_loading_overlay_to_clear()
        # The game ignores spin input while the previous round's win
        # presentation (rollup/celebration animation) is still playing —
        # confirmed: back-to-back spin() calls time out if the prior spin
        # won anything. wait_for_canvas_stable() doesn't work here (the
        # background has a continuous ambient idle animation — clouds etc.
        # — so the canvas is never byte-identical between frames even at
        # rest, confirmed by a 15s wait never succeeding). No PIXI node
        # exposes "presentation done" either, so this uses a fixed settle
        # delay based on the confirmed opCnf.spinDuration (2000ms).
        self.page.wait_for_timeout(3_000)

        def trigger() -> None:
            self.page.locator(self.CANVAS_SELECTOR).first.focus()
            self.page.keyboard.press("Space")

        return self.network_spy.wait_for_response("spin", trigger, timeout_ms=timeout_ms)

    def spin_and_wait(self) -> SpinResult:
        """Spins and returns the parsed result. If the spin triggered a
        feature (including incidentally — some forced cheat outcomes land
        Bonus symbols as a side effect, e.g. "6 OAK AA"), the result is
        captured first and then the feature is auto-resolved (see
        resolve_pending_feature()) so the caller always gets back a clean,
        spinnable base-game state."""
        exchange = self.spin()
        result = parse_spin_response(exchange.response_body)
        if result.is_feature_triggered:
            self.resolve_pending_feature()
        return result

    def spin_and_wait_feature_trigger_only(self) -> SpinResult:
        """Like spin_and_wait(), but does NOT auto-resolve a triggered
        feature — for interruption/recovery tests that need to inspect or
        interrupt the game while still mid-feature, rather than ending on a
        clean base-game state. Asserts the spin actually triggered a
        feature, since callers rely on that."""
        exchange = self.spin()
        result = parse_spin_response(exchange.response_body)
        assert result.is_feature_triggered, "expected this forced spin to trigger a feature"
        return result

    def is_feature_choice_visible(self) -> bool:
        return self.get_pixi_node_or_none(self.FEATURE_CHOICE_TITLE_NODE) is not None

    def choose_free_spins_feature(self, which: str, timeout_ms: int = 30_000) -> None:
        """which: "sticky" or "raining".

        Retries the click until the choice screen actually closes, instead
        of clicking once and trusting it registered. Confirmed live (25 Oct
        2026) that a single click here can silently fail to register —
        every test later in the same run that calls this and moves on
        immediately then times out on its next spin attempt, because the
        choice was never actually submitted server-side (the choice screen
        is still showing, consuming every subsequent Space press) while
        `unfinishedInfo` reports nothing pending — a stuck state neither of
        this project's two usual recovery checks (`unfinishedInfo`,
        `is_base_game_ready()`) can detect, so it was never caught by
        `ensure_base_game_ready()` either. Retrying the click here, at the
        source, is more reliable than trying to detect this after the fact
        everywhere it's used."""
        label = "STICKY WILDS" if which == "sticky" else "RAINING WILDS"

        def choice_screen_closed() -> bool:
            if self.get_pixi_node_or_none(self.FEATURE_CHOICE_TITLE_NODE) is None:
                return True
            try:
                self.click_pixi_text(label)
            except RuntimeError:
                pass
            return False

        self.wait_for(choice_screen_closed, timeout_ms=timeout_ms, interval_ms=1_000)

    def play_feature_spins_to_completion(self, max_spins: int = 30, response_timeout_ms: int = 15_000) -> None:
        """Plays out an active Free Spins round by pressing Space repeatedly
        until no further /feature responses arrive (round complete).

        Each iteration waits out the same win-presentation settle delay used
        by spin() before pressing Space again. Without it, a feature spin
        that wins is followed by a Space press the game silently ignores
        (still playing the celebration), the wait_for_response() below times
        out, and the loop treats that as "round complete" while spins
        actually remain — confirmed live: a round stuck at "13 OUT OF 15
        FREE SPINS" across repeated resolve attempts, because every attempt
        hit this same premature exit.

        Settle wait and response timeout were both widened (5s / 15s) after
        confirming live that a single big multi-wild-win celebration can
        still exceed the original 3s/8s budget (observed stuck at "11 OUT OF
        15" with 3 stacked WILD multipliers, across a *second* independent
        session-corruption incident on 25 Oct 2026). Each miss also gets one
        retry press before the loop gives up, since a too-early Space press
        during a still-settling celebration is silently dropped by the game
        rather than queued — a single retry recovers from exactly that race
        without having to prove a universal timing bound.

        Also dismisses any "Congratulations" popup before each press, not
        just at the very end — confirmed live (a *third* session-corruption
        incident, 25 Oct 2026): this same popup shape can appear MID-round
        with a lower spin count (e.g. "YOU HAVE WON 12 FREESPINS ... YOU
        HAVE 2 SPINS LEFT"), i.e. a retrigger grants more spins partway
        through — not just at the round's natural end. The loop previously
        only checked for it once resolve_pending_feature() finished playing
        spins, so a mid-round retrigger popup silently absorbed every Space
        press until the retry budget ran out, miscounting the round as
        "complete" while spins actually remained."""
        for _ in range(max_spins):
            self.dismiss_congrats_popup_if_present()
            self.wait_for_loading_overlay_to_clear()
            self.page.wait_for_timeout(5_000)
            try:
                self.network_spy.wait_for_response("feature", self.press_space_bar, timeout_ms=response_timeout_ms)
                continue
            except PlaywrightTimeoutError:
                pass

            # One retry: the previous press may have been silently dropped
            # mid-celebration (or behind a mid-round retrigger popup) rather
            # than the round actually being over.
            self.dismiss_congrats_popup_if_present()
            self.wait_for_loading_overlay_to_clear()
            self.page.wait_for_timeout(5_000)
            try:
                self.network_spy.wait_for_response("feature", self.press_space_bar, timeout_ms=response_timeout_ms)
            except PlaywrightTimeoutError:
                break

    def dismiss_connection_error_if_present(self, timeout_ms: int = 5_000) -> None:
        """Dismisses the "Info / The game connection was interrupted ...
        Error Code: 9999" dialog if present — confirmed live (25 Oct 2026)
        shown by the game itself on real connectivity loss, with a "Close"
        button. Tried as a real DOM element first (it renders crisp/
        anti-aliased unlike the surrounding canvas content, suggesting a
        platform-level overlay rather than a PIXI node, the same pattern as
        the Rules/Paytable panel), falling back to a PIXI click in case it's
        canvas-rendered after all. No-op if neither finds it (dialog not
        showing)."""
        try:
            close_button = self.page.get_by_text("Close", exact=True)
            if close_button.count() > 0 and close_button.first.is_visible():
                close_button.first.click()
                return
        except Exception:
            pass
        try:
            self.click_pixi_text("Close")
        except RuntimeError:
            pass

    def dismiss_congrats_popup_if_present(self, timeout_ms: int = 5_000) -> None:
        if self.get_pixi_node_or_none(self.CONGRATS_TEXT_NODE) is None:
            return
        for label in ("OK", "Close"):
            try:
                self.click_pixi_text(label)
                self.wait_for(lambda: self.get_pixi_node_or_none(self.CONGRATS_TEXT_NODE) is None, timeout_ms=timeout_ms)
                return
            except (RuntimeError, TimeoutError):
                continue

    def resolve_pending_feature(self, timeout_ms: int = 30_000) -> None:
        """Resolves a Free Spins choice/round/congrats popup so the session
        returns to a clean, spinnable base-game state. Picks Sticky Wilds
        arbitrarily when a choice is offered.

        Doesn't gate on is_feature_choice_visible()/a single flag: confirmed
        unreliable (the choice popup's title node can remain visible=true
        even once superseded by a later popup, the same stale-visible-flag
        issue seen elsewhere in this game). Instead each step is attempted
        in sequence and skipped if it doesn't apply to the current state."""
        if self.get_pixi_node_or_none(self.FEATURE_CHOICE_TITLE_NODE) is not None:
            try:
                self.choose_free_spins_feature("sticky", timeout_ms=30_000)
            except TimeoutError:
                pass

        self.dismiss_congrats_popup_if_present()
        self.play_feature_spins_to_completion()

        # The final free spin's win rollup (and the "Congratulations" summary
        # that follows it) can take noticeably longer to settle than a
        # mid-round spin's, especially with stacked wild multipliers —
        # confirmed live: is_base_game_ready() (megawaysText) reports ready
        # while the final spin's reel-stop/rollup animation is still
        # visually playing, same stale-signal issue documented elsewhere in
        # this game. Wait for the congrats popup to actually appear (a real
        # "the round has finished settling" signal) before dismissing it;
        # if this feature variant doesn't show one, fall back to one more
        # blanket settle wait.
        try:
            self.wait_for(lambda: self.get_pixi_node_or_none(self.CONGRATS_TEXT_NODE) is not None, timeout_ms=10_000)
        except (RuntimeError, TimeoutError):
            self.page.wait_for_timeout(5_000)
        self.dismiss_congrats_popup_if_present()

        self.wait_for(self.is_base_game_ready, timeout_ms=timeout_ms)
        self.wait_for_loading_overlay_to_clear(timeout_ms=timeout_ms)

    def press_space_bar(self) -> None:
        """Presses Space once without waiting for a spin response. Use
        spin()/spin_and_wait() for a normal spin; use this for negative
        tests (e.g. verifying Space does NOT spin while a panel is open)."""
        self.page.locator(self.CANVAS_SELECTOR).first.focus()
        self.page.keyboard.press("Space")

    def get_displayed_balance_text(self) -> str:
        return self.get_sibling_value_text("titleText", "BALANCE", "valueText")

    def get_displayed_bet_text(self) -> str:
        return self.get_sibling_value_text("titleText", "BET", "valueText")

    def get_displayed_ways(self) -> int:
        return self.get_displayed_integer_near_label(self.BASE_GAME_READY_NODE, "MEGAWAYS")

    def toggle_turbo(self) -> None:
        self.click_pixi_button(self.TURBO_BUTTON_NODE)

    def open_bet_panel(self) -> BetPanel:
        self.click_pixi_button(self.BET_BUTTON_NODE)
        return BetPanel(self.page)

    def open_buy_feature(self) -> BuyFeaturePanel:
        self.click_pixi_button(self.BUY_FEATURE_BUTTON_NODE)
        return BuyFeaturePanel(self.page)

    def open_auto_spin_menu(self, hold_ms: int = 2200) -> AutoSpinPanel:
        """Long-presses the spin button to open the Auto Spin menu, per the
        game rules ("click and hold the Play button for 2 seconds")."""
        bounds = self.get_pixi_node(self.SPIN_BUTTON_NODE)
        canvas_box = self.page.locator(self.CANVAS_SELECTOR).first.bounding_box()
        cx = canvas_box["x"] + bounds["x"] + bounds["width"] / 2
        cy = canvas_box["y"] + bounds["y"] + bounds["height"] / 2
        self.page.mouse.move(cx, cy)
        self.page.mouse.down()
        self.page.wait_for_timeout(hold_ms)
        self.page.mouse.up()
        return AutoSpinPanel(self.page)

    def open_info_panel(self) -> RulesPage:
        """Opens the Rules/Paytable overlay (real DOM, see RulesPage/
        PaytablePage) and returns it on the Rules tab (its default tab)."""
        self.click_pixi_button(self.INFO_BUTTON_NODE)
        return RulesPage(self.page)

    def open_paytable(self) -> PaytablePage:
        return self.open_info_panel().go_to_paytable()

    def open_cheat_panel(self) -> CheatPanel:
        """Opens the built-in QA cheat tool (requires allowCheat=true on the
        session, confirmed present in this game's init payload)."""
        panel = CheatPanel(self.page)
        panel.open()
        return panel

    def set_offline(self, offline: bool) -> None:
        """Simulates a real connectivity loss (not a mocked response) for
        interruption/recovery testing — Playwright drops all network traffic
        for this page's browser context at the transport level."""
        self.page.context.set_offline(offline)

    def dispatch_visibility_change(self, hidden: bool) -> None:
        """Dispatches the same `visibilitychange`/`document.hidden` signal a
        real browser sends when a mobile OS backgrounds the app, locks the
        device, or the user switches tasks for an incoming call. This is the
        standard web-layer signal for all of those scenarios, but it is not
        a full substitute for them: it can't reproduce OS-level process
        suspension or restore device audio, so tests using this note the gap
        explicitly rather than claiming full native-device coverage."""
        self.page.evaluate(
            """(hidden) => {
                Object.defineProperty(document, 'hidden', { value: hidden, configurable: true });
                Object.defineProperty(document, 'visibilityState', {
                    value: hidden ? 'hidden' : 'visible', configurable: true,
                });
                document.dispatchEvent(new Event('visibilitychange'));
            }""",
            hidden,
        )

    def reload_and_wait_ready(self, timeout_ms: int = 30_000) -> None:
        """Reloads the page and waits for a fresh init response plus a fully
        interactable base game, including auto-recovery of any pending round
        the reload interrupted (via ensure_base_game_ready's unfinishedInfo
        check) — the real recovery path exercised by every refresh/reload
        test case."""
        self.network_spy.wait_for_response("init", lambda: self.page.reload(), timeout_ms=timeout_ms)
        self.wait_for(self.is_loaded, timeout_ms=timeout_ms)
        self.ensure_base_game_ready(timeout_ms=timeout_ms)

    def force_next_spin(self, outcome: str) -> None:
        """Selects a forced outcome (e.g. "3 OAK BN", "6 OAK AA", "BIG WIN")
        in the built-in cheat tool and closes the panel.

        CONFIRMED NON-FUNCTIONAL in the qa environment as of 25 Oct 2026
        (DECISIONS.md D-019) — do not assume the following spin actually
        reflects `outcome`. Selecting the option does NOT reload the
        session and causes no network traffic at all (contrary to this
        method's own earlier documentation); calling the underlying
        `window.setCheatValue(outcome)` directly, and closing the panel via
        its real (but zero-size/non-Playwright-actionable) `#closeBtn`
        — in every combination, including a subsequent manual reload —
        produced no observable change in the next spin's result
        (`is_feature_triggered` stayed False, `scatter_count` stayed 0)
        across repeated live attempts, even though `allowCheat` is still
        `true` for this session. This is left in place as a best-effort,
        harmless call in case a future environment/deploy restores the
        mechanism; any test relying on it to force a result must be
        treated as blocked until D-019 is re-verified, not fixed by
        retrying harder client-side."""
        cheat_panel = self.open_cheat_panel()
        cheat_panel.select(outcome)
        self.page.evaluate("() => { const el = document.getElementById('closeBtn'); if (el) el.click(); }")
