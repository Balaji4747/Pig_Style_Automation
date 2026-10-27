from pages.base_page import BasePage


class AutoSpinPanel(BasePage):
    """Auto Spin menu, opened via GamePage.open_auto_spin_menu() (a ~2s
    long-press on the spin button). Confirmed structure (24 Oct 2026):
    spin-count options 5/10/25/50/100 (autoNumBtn, or autoNumSelectedBtn for
    the current choice), a spending-limit input, Cancel and Start."""

    SPENDING_LIMIT_INPUT_NODE = "spendingLimitInput"
    SPENDING_MIN_TEXT_NODE = "spendingMinLimitText"
    SPENDING_MAX_TEXT_NODE = "spendingMaxLimitText"

    def select_spin_count(self, count: int) -> None:
        """Select a spin-count option, e.g. 25.

        Retries on a "node not found" error — same stagger-animation class
        of issue confirmed for the bet panel (D-023/D-024/D-027). Widened
        from a single 1s retry to match BetPanel.select_bet's budget (27 Oct
        2026) after the single retry still wasn't enough during a run with
        heavier server-side load."""
        for wait_ms in (1_000, 2_000, 2_000):
            try:
                self.click_pixi_text(str(count))
                return
            except RuntimeError:
                self.page.wait_for_timeout(wait_ms)
        self.click_pixi_text(str(count))

    def start(self) -> None:
        self.click_pixi_button("startBtn")

    def cancel(self) -> None:
        self.click_pixi_button("cancelBtn")

    def spending_limit_range_text(self) -> tuple[str, str]:
        return self.get_pixi_text(self.SPENDING_MIN_TEXT_NODE), self.get_pixi_text(self.SPENDING_MAX_TEXT_NODE)
