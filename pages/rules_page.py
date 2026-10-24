from pages.base_page import BasePage


class RulesPage(BasePage):
    """Rules tab of the Info overlay. Confirmed to be real DOM (not canvas)
    injected on top of the game canvas when GamePage.open_info_panel() is
    clicked — opens on this tab by default. Container: #gameRulesPanel.

    Note: the game reuses this same footer-nav/data-section/data-common
    pattern for both #gameRulesPanel (Rules/Paytable) and #historyPanel
    (History), each with its own close button (#close_btn vs #h-close_btn).
    Don't use unscoped `.footer-item` selectors — scope to PANEL_SELECTOR.
    """

    PANEL_SELECTOR = "#gameRulesPanel"
    CLOSE_BUTTON_SELECTOR = "#close_btn"
    RULES_TAB_SELECTOR = f'{PANEL_SELECTOR} .footer-item[data-section="rules"]'
    PAYTABLE_TAB_SELECTOR = f'{PANEL_SELECTOR} .footer-item[data-section="paytable"]'

    # Confirmed live values (qa env, 23 Oct 2026) — resolves OBS-09.
    MIN_BET_SELECTOR = "#min-bet"
    MAX_BET_SELECTOR = "#max-bet"
    BB_MAX_BET_SELECTOR = "#bb-max-bet"
    MAX_WIN_SELECTOR = "#max-win"
    RTP_SELECTOR = "#rtp-value"

    def close(self) -> None:
        self.page.locator(self.CLOSE_BUTTON_SELECTOR).click()

    def go_to_paytable(self):
        from pages.paytable_page import PaytablePage

        self.page.locator(self.PAYTABLE_TAB_SELECTOR).click()
        return PaytablePage(self.page)

    def min_bet_text(self) -> str:
        return self.page.locator(self.MIN_BET_SELECTOR).inner_text()

    def max_bet_text(self) -> str:
        return self.page.locator(self.MAX_BET_SELECTOR).inner_text()

    def bb_max_bet_text(self) -> str:
        return self.page.locator(self.BB_MAX_BET_SELECTOR).inner_text()

    def max_win_text(self) -> str:
        return self.page.locator(self.MAX_WIN_SELECTOR).inner_text()

    def rtp_text(self) -> str:
        return self.page.locator(self.RTP_SELECTOR).inner_text()
