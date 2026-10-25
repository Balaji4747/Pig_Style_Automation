from pages.base_page import BasePage


class BetPanel(BasePage):
    """Bet selection panel, opened via GamePage.open_bet_panel(). Confirmed
    structure (24 Oct 2026): one betSelectionBtn (betSelectionSelectedBtn
    for the current level) per configured bet, each labelled with its
    formatted amount (e.g. "1.00")."""

    MIN_MAX_TEXT_NODE = "minmaxbetText"  # e.g. "Min: €0.10, Max: €25.00"
    STAKE_TEXT_NODE = "stakeText"  # currently-selected amount shown in-panel

    def select_bet(self, formatted_amount: str) -> None:
        """Select a bet level by its displayed label, e.g. "1.00".

        Retries up to twice (1s then 2s wait) on a "node not found" error —
        confirmed live (D-023) that this can transiently fail to find an
        otherwise-present, correctly-bounded bet label right after the
        panel (re)opens, most likely amid the heavy stale-PIXI-node buildup
        this game accumulates over a long session (see CLAUDE.md's
        "never trust a raw visible-nodes dump" note); a standalone repro
        found the same label readily present moments later. Widened from a
        single retry to two (D-033) after a single retry still wasn't
        enough once in a long, state-heavy flow (PS-CMP's full smoke test,
        called right after a spin) even though a diagnostic confirmed the
        target node was genuinely present with valid bounds throughout."""
        for wait_ms in (1_000, 2_000):
            try:
                self.click_pixi_text(formatted_amount)
                return
            except RuntimeError:
                self.page.wait_for_timeout(wait_ms)
        self.click_pixi_text(formatted_amount)

    def confirm(self) -> None:
        self.click_pixi_text("Set")

    def cancel(self) -> None:
        self.click_pixi_button("cancelBtn")

    def min_max_text(self) -> str:
        return self.get_pixi_text(self.MIN_MAX_TEXT_NODE)

    def stake_text(self) -> str:
        return self.get_pixi_text(self.STAKE_TEXT_NODE)
