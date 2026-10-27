from pages.base_page import BasePage


class PaytablePage(BasePage):
    """Paytable tab of the Info overlay. Real DOM (not canvas), confirmed
    live. Reached via RulesPage.go_to_paytable() or GamePage.open_paytable().

    Per-symbol payout grid confirmed live (27 Oct 2026):
    .symbol-payout-grid contains one .treasure-item[data-symbol="AA"] (etc.)
    per paying symbol, each with one .level-row per OAK count (6/5/4/3) -
    a level-number <span>, a ":" <span>, and a `.points-amount` <span> whose
    text is the CURRENCY value already scaled to the current total bet
    (confirmed: AA 6-OAK showed "€7.50" at bet €1.00 = 150 credits * 1.00 /
    20 exactly) - not a flat credit value or multiplier."""

    PANEL_SELECTOR = "#gameRulesPanel"
    CLOSE_BUTTON_SELECTOR = "#close_btn"
    RULES_TAB_SELECTOR = f'{PANEL_SELECTOR} .footer-item[data-section="rules"]'
    HEADING_SELECTOR = '[data-common="paytableHeading"]'
    PAY_TABLE_SELECTOR = "#pay_table"
    SYMBOL_ITEM_SELECTOR = ".symbol-payout-grid .treasure-item"

    def close(self) -> None:
        self.page.locator(self.CLOSE_BUTTON_SELECTOR).click()

    def go_to_rules(self):
        from pages.rules_page import RulesPage

        self.page.locator(self.RULES_TAB_SELECTOR).click()
        return RulesPage(self.page)

    def is_displayed(self) -> bool:
        return self.page.locator(self.HEADING_SELECTOR).is_visible()

    def symbol_payout_text(self, symbol: str, oak_count: int) -> str:
        """The displayed currency payout (e.g. "€7.50") for `symbol` at
        `oak_count` (3-6), at whatever bet is currently selected."""
        item = self.page.locator(f'{self.SYMBOL_ITEM_SELECTOR}[data-symbol="{symbol}"]')
        rows = item.locator(".level-row")
        for i in range(rows.count()):
            row = rows.nth(i)
            level_text = row.locator("span").first.inner_text().strip()
            if level_text == str(oak_count):
                return row.locator(".points-amount").inner_text()
        raise RuntimeError(f"No level-row found for {symbol} {oak_count}-OAK")
