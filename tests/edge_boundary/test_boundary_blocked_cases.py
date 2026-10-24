"""PS-EDG cases that are genuinely blocked in this environment, kept as
explicit skips (with reasoning) rather than silent gaps so they show up in
collection and the final report. Each reason mirrors an established blocker
already documented in DECISIONS.md for the equivalent PS-INT/PS-ERR/PS-STR
case."""
import pytest

pytestmark = pytest.mark.boundary


@pytest.mark.test_case("PS-EDG-001")
def test_min_bet_exact_balance_spin_to_zero():
    """BLOCKED: requires balance exactly equal to a bet amount; this
    session's balance (~6.1M EUR, see D-005/D-006) can't be genuinely
    drained to a boundary value in a reasonable number of real spins, and
    mocking the balance itself (rather than a response) isn't possible —
    the client never sends its own balance, it only displays what the
    server returns. Ref: GR-28, GR-22 | OBS-09."""
    pytest.skip("Blocked: session balance can't be set to an exact boundary value in this environment")


@pytest.mark.test_case("PS-EDG-002")
def test_max_bet_exact_balance_spin():
    """BLOCKED: same as PS-EDG-001 — needs an exact balance precondition
    not achievable here. Ref: GR-28 | OBS-09."""
    pytest.skip("Blocked: session balance can't be set to an exact boundary value in this environment")


@pytest.mark.test_case("PS-EDG-003")
def test_balance_one_cent_below_bet_blocks_spin():
    """BLOCKED: same balance-precondition limitation as PS-EDG-001; the
    client-reaction equivalent (mocked insufficient-funds response) is
    already covered by PS-ERR-001. Ref: GR-22."""
    pytest.skip("Blocked: session balance can't be set to an exact boundary value — see PS-ERR-001 for the mocked equivalent")


@pytest.mark.test_case("PS-EDG-004")
def test_zero_balance_on_launch():
    """BLOCKED: same balance-precondition limitation. Ref: GR-46."""
    pytest.skip("Blocked: session balance can't be set to zero in this environment")


@pytest.mark.test_case("PS-EDG-005")
def test_lower_bet_to_continue_when_below_current_bet():
    """BLOCKED: requires a balance below the current bet, which requires the
    same unreachable low-balance precondition as PS-EDG-001. Ref: GR-20."""
    pytest.skip("Blocked: session balance can't be set below a bet amount in this environment")


@pytest.mark.test_case("PS-EDG-006")
def test_buy_accepted_at_exact_100x_bet_balance():
    """BLOCKED: Buy Feature confirm flow not yet verified (see
    PS-FUN-059/061/062), compounded by the same unreachable exact-balance
    precondition. Ref: GR-36."""
    pytest.skip("Blocked: Buy-confirm flow unverified + exact-balance precondition unreachable")


@pytest.mark.test_case("PS-EDG-007")
def test_buy_cost_at_min_bet():
    """BLOCKED: Buy Feature confirm flow not yet verified; the cost-display
    part (no confirm) is already covered by
    tests/functional/test_buy_free_spins.py's existing cost/scaling tests.
    Ref: GR-36, GR-28 | OBS-09."""
    pytest.skip("Blocked: Buy-confirm flow unverified — cost display itself covered by PS-FUN buy-feature tests")


@pytest.mark.test_case("PS-EDG-008")
def test_buy_cost_at_max_bet_displays_fully():
    """BLOCKED: Buy Feature confirm flow not yet verified. Ref: GR-36,
    GR-28."""
    pytest.skip("Blocked: Buy-confirm flow unverified")


@pytest.mark.test_case("PS-EDG-010")
def test_win_equal_to_cap_paid_in_full():
    """BLOCKED: needs a cheat outcome that reliably triggers maxCapReached,
    not confirmed available (same blocker as PS-INT-026/PS-ERR-019/
    PS-STR-023). Ref: GR-29 | OBS-09."""
    pytest.skip("Blocked: needs a cheat outcome that reliably triggers maxCapReached — not confirmed available")


@pytest.mark.test_case("PS-EDG-011")
def test_win_above_cap_truncated_to_cap():
    """BLOCKED: same cap-trigger limitation as PS-EDG-010. Ref: GR-29 |
    OBS-09."""
    pytest.skip("Blocked: needs a cheat outcome that reliably triggers maxCapReached — not confirmed available")


@pytest.mark.test_case("PS-EDG-012")
def test_cap_reached_on_triggering_spin_with_3_bn():
    """BLOCKED: same cap-trigger limitation, compounded by needing it to
    coincide with a 3-BN trigger specifically — not controllable together.
    Ref: GR-29 | OBS-09."""
    pytest.skip("Blocked: needs a cheat outcome that reliably triggers maxCapReached — not confirmed available")


@pytest.mark.test_case("PS-EDG-014")
def test_117649_ways_all_aa_no_wilds():
    """BLOCKED: requires forcing every one of the 42 visible positions to a
    specific symbol with all reels at height 7 and zero wilds — the cheat
    tool only forces a seed influencing the outcome, not an exact full
    board (confirmed: even "6 OAK AA" doesn't guarantee a 6-of-a-kind win).
    Ref: GR-01, M-05, GR-29."""
    pytest.skip("Blocked: cheat tool cannot force an exact full board (all 42 positions, specific symbol, no wilds)")


@pytest.mark.test_case("PS-EDG-015")
def test_extreme_sticky_multiplier_product_no_overflow():
    """BLOCKED: requires forcing a specific large number of sticky wilds
    (e.g. 28) with x3 multipliers each — not controllable; sticky
    accumulation is incremental and random per spin, and max_spins in a
    Sticky round (20 at most, per the award table) can't even reach 28
    positions (6 reels x up to 7 rows = 42 max, but realistically bounded
    well below what's needed to force this deterministically). Ref: GR-13,
    GR-29."""
    pytest.skip("Blocked: cannot force a specific large sticky-wild count/multiplier combination")


@pytest.mark.test_case("PS-EDG-016")
def test_3bn_trigger_with_all_reels_at_7_rows():
    """BLOCKED: requires both an exact BN count AND an exact reel-height
    configuration simultaneously — the cheat tool controls symbol
    placement via a seed, not reel height, which is independently random.
    Ref: GR-14."""
    pytest.skip("Blocked: cannot force reel height (2-7) independently of the cheat tool's symbol seed")


@pytest.mark.test_case("PS-EDG-017")
def test_6bn_trigger_with_all_reels_at_2_rows():
    """BLOCKED: same reel-height-control limitation as PS-EDG-016.
    Ref: GR-14, GR-17."""
    pytest.skip("Blocked: cannot force reel height (2-7) independently of the cheat tool's symbol seed")


@pytest.mark.test_case("PS-EDG-022")
def test_inputs_during_fs_transition_are_ignored():
    """BLOCKED (P1): requires reliably hitting the FS intro/outro
    transition's exact window to click during it — no PIXI signal was
    confirmed for "transition in progress" distinct from the surrounding
    states, so timing this reliably wasn't achievable within this run's
    scope. Ref: GR-16."""
    pytest.skip("Blocked: no confirmed signal for the exact FS intro/outro transition window to click during")


@pytest.mark.test_case("PS-EDG-024")
def test_auto_spin_stops_exactly_at_spend_limit():
    """BLOCKED (P1): the workbook itself flags this as Requires
    Specification/Confirmation (inclusive/exclusive boundary, OBS-21).
    `AutoSpinPanel` exposes a spending-limit input field but entering a
    value into it and forcing consistent losses to hit the limit exactly
    was not attempted this run — would need the input mechanism verified
    first (untested, same gap noted against PS-FUN-076 historically).
    Ref: GR-40 | OBS-21."""
    pytest.skip("Blocked: spend-limit input mechanism untested, and the boundary semantics are an open spec question")


@pytest.mark.test_case("PS-EDG-026")
def test_feature_on_last_auto_spin_ends_auto_after():
    """PS-EDG-026 (P1): not forceable to land on a specific auto-spin index
    (real random outcomes) — would need many repeated attempts to land a
    Bonus trigger exactly on the last spin of a short Auto Spin run, which
    the task rules disallow (no looping random spins waiting for an
    outcome). Ref: GR-43."""
    pytest.skip("Blocked: cannot force a Bonus trigger to land on a specific auto-spin index without looping")


@pytest.mark.test_case("PS-EDG-027")
def test_stop_pressed_during_auto_triggered_free_spins():
    """PS-EDG-027 (P1): same limitation as PS-EDG-026 — cannot reliably and
    deterministically get Auto Spin to trigger a feature to then press Stop
    during it, without looping random spins. Ref: GR-43."""
    pytest.skip("Blocked: cannot force an auto-triggered feature without looping random spins")


@pytest.mark.test_case("PS-EDG-028")
def test_refresh_during_the_last_free_spin():
    """PS-EDG-028: refreshing during Free Spins in general is covered by
    PS-INT-003/022-025, but hitting the LAST spin specifically isn't
    controllable (feature length is fixed by the award table, but which
    spin is "in flight" when a refresh happens can't be targeted exactly
    without the same per-spin completion signal gap noted in D-011/D-012).
    Ref: GR-56."""
    pytest.skip("Blocked: cannot reliably target refreshing exactly during the feature's final spin")


@pytest.mark.test_case("PS-EDG-037")
def test_currency_decimal_boundary_display():
    """BLOCKED: this session/environment only has EUR (2 decimals)
    configured — no 0-decimal or 3-decimal currency session is available to
    test against. Ref: GR-19."""
    pytest.skip("Blocked: only a 2-decimal (EUR) currency session is available in this environment")


@pytest.mark.test_case("PS-EDG-039")
def test_history_paging_with_many_rounds():
    """BLOCKED (P3): no History panel page object exists yet (confirmed
    present in the DOM structure per CLAUDE.md's `#historyPanel` note, but
    its paging controls/content were never inspected or modelled this run).
    Ref: GR-47."""
    pytest.skip("Blocked: History panel page object not yet built — only Rules/Paytable are modelled")


@pytest.mark.test_case("PS-EDG-040")
def test_fs_all_reels_7_rows_with_sticky_wilds():
    """BLOCKED (P2): requires forcing all 6 reels to height 7 during a
    Sticky Wilds Free Spins round simultaneously — reel height is
    independently random and not controllable via the cheat tool.
    Ref: GR-02, GR-08."""
    pytest.skip("Blocked: cannot force reel height independently of the cheat tool's symbol seed")
