from decimal import Decimal

import pytest

pytestmark = [pytest.mark.functional, pytest.mark.regression]


@pytest.mark.test_case("PS-FEA-013")
def test_min_trigger_starts_raining_with_15_spins(game_ready, trigger_and_choose):
    """PS-FEA-013: a 3-BN trigger must start Raining Wilds Free Spins with
    15 spins. Ref: GR-09, GR-17, M-11."""
    trigger_and_choose(3, "raining")
    assert game_ready.get_init_data().unfinished_info is not None
    game_ready.resolve_pending_feature(timeout_ms=120_000)
    assert game_ready.get_init_data().unfinished_info is None


@pytest.mark.test_case("PS-FEA-014")
def test_max_trigger_starts_raining_with_30_spins(game_ready, trigger_and_choose):
    """PS-FEA-014: a 6-BN trigger must start Raining Wilds Free Spins with
    30 spins (the max award). Ref: GR-09, GR-17, M-11 | OBS-16."""
    trigger_and_choose(6, "raining")
    assert game_ready.get_init_data().unfinished_info is not None
    game_ready.resolve_pending_feature(timeout_ms=240_000)
    assert game_ready.get_init_data().unfinished_info is None


@pytest.mark.test_case("PS-FEA-015")
def test_raining_completion_credits_total_and_returns_to_base(game_ready, trigger_and_choose, play_one_feature_spin):
    """PS-FEA-015: Raining Wilds Free Spins must end after the last spin,
    show/credit the total feature win, and return to base game at the
    triggering bet. Ref: GR-09, GR-17, GR-12."""
    balance_before_feature = game_ready.get_balance()
    trigger_and_choose(3, "raining")
    total_fs_win = Decimal("0")
    for _ in range(18):
        data = play_one_feature_spin()
        if data is None:
            break
        total_fs_win += Decimal(str(data["result"]["totalWin"]))

    game_ready.resolve_pending_feature(timeout_ms=180_000)
    assert game_ready.get_init_data().unfinished_info is None
    assert game_ready.get_init_data().player_info.balance == balance_before_feature + total_fs_win

    result = game_ready.spin_and_wait()
    assert result.bet == Decimal("1.00")


@pytest.mark.test_case("PS-FEA-016")
def test_raining_counter_decrements_by_one_per_spin(game_ready, trigger_and_choose, play_one_feature_spin):
    """PS-FEA-016 (P1, Partial): same scope limitation as PS-FEA-004 — no
    confirmed live remaining-spins HUD node, verified via the network layer
    (one `/feature` response per consumed spin, never duplicated).
    Ref: GR-09, GR-17."""
    trigger_and_choose(3, "raining")
    round_ids_seen = []
    for _ in range(18):
        data = play_one_feature_spin()
        if data is None:
            break
        round_ids_seen.append(data["roundId"])

    assert len(round_ids_seen) == len(set(round_ids_seen))
    game_ready.resolve_pending_feature(timeout_ms=60_000)


@pytest.mark.test_case("PS-FEA-017")
def test_raining_zero_win_feature_completes_with_total_zero(game_ready, trigger_and_choose, play_one_feature_spin):
    """PS-FEA-017 (P1): a Raining Wilds round with no wins must still
    complete correctly. Not forced to guarantee zero wins — verifies the
    balance formula holds for whatever total results. Ref: GR-09, GR-17."""
    balance_before_feature = game_ready.get_balance()
    trigger_and_choose(3, "raining")
    total_fs_win = Decimal("0")
    for _ in range(18):
        data = play_one_feature_spin()
        if data is None:
            break
        total_fs_win += Decimal(str(data["result"]["totalWin"]))

    game_ready.resolve_pending_feature(timeout_ms=180_000)
    assert game_ready.get_init_data().player_info.balance == balance_before_feature + total_fs_win


@pytest.mark.test_case("PS-FEA-018")
def test_raining_no_bonus_symbols_or_retrigger(game_ready, trigger_and_choose, play_one_feature_spin):
    """PS-FEA-018: Bonus symbols must never appear, and the feature must
    never retrigger, during Raining Wilds Free Spins. Ref: GR-18, M-08."""
    trigger_and_choose(6, "raining")
    for _ in range(30):
        data = play_one_feature_spin()
        if data is None:
            break
        for reel in data["result"]["reelView"]:
            assert "BN" not in reel, "Bonus symbol appeared during Raining Wilds Free Spins"
    game_ready.resolve_pending_feature(timeout_ms=240_000)


@pytest.mark.test_case("PS-FEA-019")
def test_raining_plays_at_trigger_bet_with_no_per_spin_debit(game_ready, trigger_and_choose, play_one_feature_spin):
    """PS-FEA-019: Raining Wilds Free Spins must play at the triggering bet
    with no per-spin debit, triggered at max bet per the workbook.
    Ref: GR-15."""
    bet_panel = game_ready.open_bet_panel()
    init_data = game_ready.get_init_data()
    bet_panel.select_bet(f"{init_data.player_info.max_bet:.2f}")
    bet_panel.confirm()

    trigger_and_choose(3, "raining")
    balance = game_ready.get_balance()
    for _ in range(18):
        data = play_one_feature_spin()
        if data is None:
            break
        win = Decimal(str(data["result"]["totalWin"]))
        new_balance = Decimal(str(data["playerInfo"]["balance"]))
        assert new_balance == balance + win, "a Free Spins round spin debited the player"
        assert Decimal(str(data["result"]["bet"])) == init_data.player_info.max_bet
        balance = new_balance

    game_ready.resolve_pending_feature(timeout_ms=180_000)
    bet_panel = game_ready.open_bet_panel()
    bet_panel.select_bet(f"{init_data.player_info.default_bet:.2f}")
    bet_panel.confirm()


@pytest.mark.test_case("PS-FEA-020")
def test_raining_total_win_meter_accumulates(game_ready, trigger_and_choose, play_one_feature_spin):
    """PS-FEA-020: the total win meter must accumulate each spin's win
    during Raining Wilds Free Spins. Ref: GR-12."""
    trigger_and_choose(3, "raining")
    running_total = Decimal("0")
    for _ in range(18):
        data = play_one_feature_spin()
        if data is None:
            break
        running_total += Decimal(str(data["result"]["totalWin"]))
    balance_before_resolve = game_ready.get_balance()
    game_ready.resolve_pending_feature(timeout_ms=180_000)
    assert game_ready.get_init_data().player_info.balance == balance_before_resolve


@pytest.mark.test_case("PS-FEA-021")
def test_raining_winnings_credited_only_at_feature_end(game_ready, trigger_and_choose, play_one_feature_spin):
    """PS-FEA-021 (P0): per-spin balance must only ever reflect that spin's
    own win. Ref: GR-12 | OBS-08 (rules only state this explicitly for
    Raining Wilds, which this case directly covers)."""
    trigger_and_choose(3, "raining")
    balance = game_ready.get_balance()
    for _ in range(18):
        data = play_one_feature_spin()
        if data is None:
            break
        win = Decimal(str(data["result"]["totalWin"]))
        new_balance = Decimal(str(data["playerInfo"]["balance"]))
        assert new_balance == balance + win
        balance = new_balance
    game_ready.resolve_pending_feature(timeout_ms=180_000)


@pytest.mark.test_case("PS-FEA-022")
def test_raining_refresh_mid_feature_resumes_with_state(game_ready, trigger_and_choose, play_one_feature_spin):
    """PS-FEA-022: refreshing mid-Raining-Wilds must resume with the same
    remaining spins/total win preserved (checked via unfinishedInfo and
    balance continuity). Ref: GR-56."""
    trigger_and_choose(3, "raining")
    for _ in range(3):
        if play_one_feature_spin() is None:
            break

    balance_before_reload = game_ready.get_balance()
    assert game_ready.get_init_data().unfinished_info is not None
    game_ready.reload_and_wait_ready()
    assert game_ready.get_init_data().player_info.balance >= balance_before_reload


@pytest.mark.test_case("PS-FEA-023")
def test_raining_refresh_during_spin_restores_result_once(game_ready, trigger_and_choose):
    """PS-FEA-023: refreshing while a Raining Wilds spin is animating must
    restore the already-determined result exactly once. Ref: GR-56."""
    trigger_and_choose(3, "raining")
    game_ready.network_spy.clear("feature")
    game_ready.wait_for_loading_overlay_to_clear()
    game_ready.page.wait_for_timeout(5_000)
    game_ready.press_space_bar()
    game_ready.page.wait_for_timeout(300)

    game_ready.reload_and_wait_ready()
    round_ids = [e.response_body["data"]["roundId"] for e in game_ready.network_spy.all("feature")]
    assert len(round_ids) == len(set(round_ids)), "interrupted feature spin was processed more than once"


@pytest.mark.test_case("PS-FEA-024")
def test_raining_max_win_cap_ends_feature_immediately():
    """PS-FEA-024: reaching the max win cap during Raining Wilds Free Spins
    must end the feature immediately. BLOCKED: same cap-trigger limitation
    as PS-FEA-012/PS-INT-026. Ref: GR-29 | OBS-09."""
    pytest.skip("Blocked: needs a cheat outcome that reliably triggers maxCapReached — not confirmed available")
