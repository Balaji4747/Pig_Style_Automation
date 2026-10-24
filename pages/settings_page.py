from pages.base_page import BasePage


class SettingsPage(BasePage):
    """Menu/Settings overlay, opened via the canvas 'menuBtn' PIXI node.
    The trigger and sound toggle are confirmed; the panel's internal content
    (Lobby/History/Deposit/Promotions layout) has not been inspected yet —
    TODO once we need to automate those specific flows."""

    MENU_BUTTON_NODE = "menuBtn"
    SOUND_ON_BUTTON_NODE = "soundOnBtn"
    SOUND_OFF_BUTTON_NODE = "soundOffBtn"

    def open(self) -> None:
        self.click_pixi_button(self.MENU_BUTTON_NODE)

    def toggle_sound(self) -> None:
        if self.get_pixi_node_or_none(self.SOUND_ON_BUTTON_NODE):
            self.click_pixi_button(self.SOUND_ON_BUTTON_NODE)
        else:
            self.click_pixi_button(self.SOUND_OFF_BUTTON_NODE)
