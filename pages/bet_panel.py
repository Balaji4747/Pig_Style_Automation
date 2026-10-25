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

        Retries once after a short wait on a "node not found" error —
        confirmed live (D-023) that this can transiently fail to find an
        otherwise-present, correctly-bounded bet label right after the
        panel (re)opens, most likely amid the heavy stale-PIXI-node buildup
        this game accumulates over a long session (see CLAUDE.md's
        "never trust a raw visible-nodes dump" note); a standalone repro
        found the same label readily present moments later."""
        try:
            self.click_pixi_text(formatted_amount)
        except RuntimeError:
            self.page.wait_for_timeout(1_000)
            self.click_pixi_text(formatted_amount)

    def confirm(self) -> None:
        self.click_pixi_text("Set")

    def cancel(self) -> None:
        self.click_pixi_button("cancelBtn")

    def min_max_text(self) -> str:
        return self.get_pixi_text(self.MIN_MAX_TEXT_NODE)

    def stake_text(self) -> str:
        return self.get_pixi_text(self.STAKE_TEXT_NODE)
