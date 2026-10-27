import pytest

from utils.logger import get_logger

log = get_logger(__name__)


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.sanity
@pytest.mark.test_case("PS-REG-024")
def test_three_bonus_symbols_trigger_free_spins(game_ready, init_data):
    """PS-FUN-050: 3 Bonus symbols anywhere on the reels trigger Free Spins
    (the FS type selection screen). No cheat involved: force_next_spin() is
    confirmed unreliable in this environment (CLAUDE.md D-019; a 3+ Bonus
    trigger is also too rare to rely on landing unforced, previously making
    this case ENVIRONMENT-BLOCKED). buy_feature_and_wait() is a real,
    deterministic purchase confirmed live to always trigger with
    scatter_count >= 3, used here purely as a reliable trigger - not to test
    the Buy flow itself (see test_buy_free_spins.py / test_buy_feature.py).

    - Buy the feature at min bet
    - Assert scatter count >= 3, feature triggered, next feature is pickFeature
    - Drain the feature so later tests start clean"""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.min_bet:.2f}")
    bet_panel.confirm()

    result = game_ready.buy_feature_and_wait()
    log.info(
        "Scatter count: %s, feature triggered: %s, next feature: %s",
        result.scatter_count, result.is_feature_triggered, result.next_feature,
    )
    assert result.scatter_count >= 3
    assert result.is_feature_triggered
    assert result.next_feature == "pickFeature"

    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    try:
        game_ready.choose_free_spins_feature("sticky")
    except TimeoutError:
        pass
    game_ready.drain_active_feature_if_any()

    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()


@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.test_case("PS-REG-025")
def test_fewer_than_three_bonus_symbols_do_not_trigger(game_ready):
    """PS-FUN-051: fewer than 3 Bonus symbols do not trigger Free Spins.
    Validated as an emergent property across a batch of regular spins (the
    cheat tool only forces 3-6 OAK BN, not exactly 2) — scatter_count < 3
    must always mean is_feature_triggered is False.

    - Play 8 unforced spins
    - For each with scatter count < 3, assert feature was not triggered"""
    checked_any_scatter_below_three = False
    for i in range(8):
        result = game_ready.spin_and_wait()
        log.info("Spin %s: scatter count %s, feature triggered %s", i + 1, result.scatter_count, result.is_feature_triggered)
        if result.scatter_count < 3:
            assert not result.is_feature_triggered
            checked_any_scatter_below_three = True
    assert checked_any_scatter_below_three, "No spin with <3 scatters observed in this sample"


@pytest.mark.functional
@pytest.mark.regression
def test_bonus_symbols_do_not_pay_as_a_way(game_ready, init_data):
    """PS-FUN-053: Bonus symbols never award a ways pay (BN pay is 0 in the
    math file, confirmed in config/paytable.yaml and the live paytable). No
    cheat involved: force_next_spin() is confirmed unreliable in this
    environment (CLAUDE.md D-019) - buy_feature_and_wait() is a real,
    deterministic purchase that reliably lands 3+ Bonus symbols, used here
    purely to guarantee BN is genuinely present on the board so this check
    is meaningful, not to test the Buy flow itself.

    - Buy the feature at min bet (guarantees 3+ BN on the board)
    - Assert no win line's symbol is "BN"
    - Drain the feature so later tests start clean"""
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.min_bet:.2f}")
    bet_panel.confirm()

    result = game_ready.buy_feature_and_wait()
    log.info("Scatter count: %s, win lines: %s", result.scatter_count, [(wl.symbol, wl.win_amount) for wl in result.win_lines])
    assert all(wl.symbol != "BN" for wl in result.win_lines)

    game_ready.wait_for(
        lambda: game_ready.get_pixi_node_or_none(game_ready.FEATURE_CHOICE_TITLE_NODE) is not None, timeout_ms=15_000
    )
    try:
        game_ready.choose_free_spins_feature("sticky")
    except TimeoutError:
        pass
    game_ready.drain_active_feature_if_any()

    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()
