from pages.base_page import BasePage


class CheatPanel(BasePage):
    """Built-in QA cheat tool, present because the session has allowCheat=true
    (confirmed in the init response's playerInfo). Lets tests force a
    specific outcome on the next spin — e.g. "3 OAK BN" through "6 OAK BN"
    for bonus-trigger test cases, "<n> OAK WC" for wild-count cases, "<n> OAK
    <symbol>" for specific paytable-line cases, or "BIG WIN"/"MEGA WIN"/
    "GIGA WIN"/"UNBEL WIN"/"FEATURE_MISS"/"NONE".

    Opened via window.cheatBtnClicked() (a function the game exposes on
    window, confirmed present); options are populated via
    window.fetchCheatDetails(), which fetches assets/panel/cheat.json.
    Selecting an option reloads the game session to apply it — the forced
    outcome takes effect on the first spin after the reload, not before.
    """

    CHEAT_BUTTON_NODE = "cheatBtn"
    OPTIONS_SELECTOR = "#cheatsContainer .cheatDiv"

    def open(self) -> None:
        self.page.evaluate("() => window.cheatBtnClicked()")
        self.page.evaluate("async () => { await window.fetchCheatDetails(); }")
        self.page.wait_for_selector(self.OPTIONS_SELECTOR, timeout=self.DEFAULT_TIMEOUT_MS)

    def list_options(self) -> list[str]:
        return [t.strip() for t in self.page.locator(self.OPTIONS_SELECTOR).all_inner_texts()]

    def select(self, option_text: str) -> None:
        self.page.get_by_text(option_text, exact=True).click()
