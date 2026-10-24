from pages.base_page import BasePage


class PaytablePage(BasePage):
    """Paytable tab of the Info overlay. Real DOM (not canvas), confirmed
    live. Reached via RulesPage.go_to_paytable() or GamePage.open_paytable().
    """

    PANEL_SELECTOR = "#gameRulesPanel"
    CLOSE_BUTTON_SELECTOR = "#close_btn"
    RULES_TAB_SELECTOR = f'{PANEL_SELECTOR} .footer-item[data-section="rules"]'
    HEADING_SELECTOR = '[data-common="paytableHeading"]'
    PAY_TABLE_SELECTOR = "#pay_table"

    def close(self) -> None:
        self.page.locator(self.CLOSE_BUTTON_SELECTOR).click()

    def go_to_rules(self):
        from pages.rules_page import RulesPage

        self.page.locator(self.RULES_TAB_SELECTOR).click()
        return RulesPage(self.page)

    def is_displayed(self) -> bool:
        return self.page.locator(self.HEADING_SELECTOR).is_visible()
