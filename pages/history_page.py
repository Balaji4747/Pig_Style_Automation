from pages.base_page import BasePage


class HistoryPage(BasePage):
    """History tab of the Info overlay, a footer-nav section inside the same
    DOM panel as Rules/Paytable (sibling of RulesPage/PaytablePage, not a
    subclass — same pattern: reused #gameRulesPanel container, scoped
    footer-item selectors). Reached via RulesPage/PaytablePage's shared
    footer-nav, data-section="history". Confirmed live (27 Oct 2026):
    container #historyPanel, close button #h-close_btn, rows under
    #tableBody as .bet-row elements. No pagination controls exist — all
    recent rounds render in one scrollable list."""

    PANEL_SELECTOR = "#historyPanel"
    CLOSE_BUTTON_SELECTOR = "#h-close_btn"
    ROW_SELECTOR = f"{PANEL_SELECTOR} .bet-row"

    def is_displayed(self) -> bool:
        return self.page.locator(self.PANEL_SELECTOR).is_visible()

    def row_count(self) -> int:
        return self.page.locator(self.ROW_SELECTOR).count()

    def row_by_round_id(self, round_id: str):
        return self.page.locator(f'{self.ROW_SELECTOR}:has(.round-id-copy[data-round-id="{round_id}"])').first

    def row_type(self, row) -> str:
        return row.locator(".type-badge").first.inner_text()

    def row_bet_amount(self, row) -> str:
        return row.locator(".amount-column.bet-amount").first.inner_text()

    def row_win_amount(self, row) -> str:
        return row.locator(".amount-column.win-amount").first.inner_text()

    def close(self) -> None:
        self.page.locator(self.CLOSE_BUTTON_SELECTOR).click()
