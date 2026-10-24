from pages.base_page import BasePage


class BuyFeaturePanel(BasePage):
    """Buy Feature (Buy Free Spins) panel, opened via GamePage.open_buy_feature().
    Confirmed structure (24 Oct 2026)."""

    COST_TEXT_NODE = "buyFreeSpinsValueText"  # e.g. "€100.00"
    STAKE_TEXT_NODE = "stakeText"  # base bet shown in this panel, e.g. "€1.00"

    def cost_text(self) -> str:
        return self.get_pixi_text(self.COST_TEXT_NODE)

    def stake_text(self) -> str:
        return self.get_pixi_text(self.STAKE_TEXT_NODE)

    def confirm(self) -> None:
        self.click_pixi_text("Buy bonus")

    def cancel(self) -> None:
        self.click_pixi_button("cancelBtn")
