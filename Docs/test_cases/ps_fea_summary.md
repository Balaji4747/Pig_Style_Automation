# Feature Testing - Summary

Columns exactly as found in workbook: ['Test Case ID', 'Module', 'Feature', 'Sub-Feature', 'Test Scenario', 'Preconditions', 'Test Data', 'Detailed Test Steps', 'Expected Result', 'Actual Result', 'Priority', 'Severity', 'Test Type', 'Automation Candidate', 'Environment', 'Browser/Device', 'Status', 'Defect ID', 'Remarks']

Total data rows: 59

## Priority x Automation Candidate breakdown

| Priority | Automation Candidate | Count |
|---|---|---|
| P0 | No | 1 |
| P0 | Yes | 39 |
| P1 | No | 2 |
| P1 | Partial | 5 |
| P1 | Yes | 11 |
| P2 | Partial | 1 |

## Full row list (ID | Priority | Automation Candidate | Scenario)

| Test Case ID | Priority | Automation Candidate | Test Scenario |
|---|---|---|---|
| PS-FEA-001 | P0 | Yes | Verify minimum trigger (3 BN) starts Sticky Wilds FS with 7 spins |
| PS-FEA-002 | P0 | Yes | Verify maximum trigger (6 BN) starts Sticky Wilds FS with 20 spins |
| PS-FEA-003 | P0 | Yes | Verify Sticky Wilds FS ends after the last spin and shows total feature win, then returns to base game |
| PS-FEA-004 | P1 | Yes | Verify the Free Spins counter decrements by exactly 1 per spin in Sticky Wilds FS |
| PS-FEA-005 | P1 | Yes | Verify Sticky Wilds FS with no wins completes correctly showing total 0.00 |
| PS-FEA-006 | P0 | Yes | Verify Bonus symbols do not appear and feature cannot retrigger in Sticky Wilds FS |
| PS-FEA-007 | P0 | Yes | Verify Sticky Wilds FS plays at trigger bet with no per-spin debit |
| PS-FEA-008 | P0 | Yes | Verify total win meter accumulates each spin win during Sticky Wilds FS |
| PS-FEA-009 | P0 | Yes | Verify when Sticky Wilds FS winnings reach the player balance |
| PS-FEA-010 | P0 | Yes | Verify Sticky Wilds FS resumes after browser refresh with same remaining spins, wilds and total win |
| PS-FEA-011 | P0 | Yes | Verify refresh while a Sticky Wilds FS spin is animating restores the already-determined result |
| PS-FEA-012 | P0 | Yes | Verify reaching max win cap during Sticky Wilds FS ends the feature immediately |
| PS-FEA-013 | P0 | Yes | Verify minimum trigger (3 BN) starts Raining Wilds FS with 15 spins |
| PS-FEA-014 | P0 | Yes | Verify maximum trigger (6 BN) starts Raining Wilds FS with 30 spins |
| PS-FEA-015 | P0 | Yes | Verify Raining Wilds FS ends after the last spin and shows total feature win, then returns to base game |
| PS-FEA-016 | P1 | Yes | Verify the Free Spins counter decrements by exactly 1 per spin in Raining Wilds FS |
| PS-FEA-017 | P1 | Yes | Verify Raining Wilds FS with no wins completes correctly showing total 0.00 |
| PS-FEA-018 | P0 | Yes | Verify Bonus symbols do not appear and feature cannot retrigger in Raining Wilds FS |
| PS-FEA-019 | P0 | Yes | Verify Raining Wilds FS plays at trigger bet with no per-spin debit |
| PS-FEA-020 | P0 | Yes | Verify total win meter accumulates each spin win during Raining Wilds FS |
| PS-FEA-021 | P0 | Yes | Verify when Raining Wilds FS winnings reach the player balance |
| PS-FEA-022 | P0 | Yes | Verify Raining Wilds FS resumes after browser refresh with same remaining spins, wilds and total win |
| PS-FEA-023 | P0 | Yes | Verify refresh while a Raining Wilds FS spin is animating restores the already-determined result |
| PS-FEA-024 | P0 | Yes | Verify reaching max win cap during Raining Wilds FS ends the feature immediately |
| PS-FEA-025 | P0 | Yes | Verify a Sticky Wild remains in its reel for all remaining Free Spins |
| PS-FEA-026 | P0 | Yes | Verify a Sticky Wild keeps its assigned multiplier for the rest of the feature |
| PS-FEA-027 | P0 | Yes | Verify each landing Sticky Wild shows its assigned multiplier |
| PS-FEA-028 | P1 | Yes | Verify Sticky Wilds land only on reels 2-5 |
| PS-FEA-029 | P1 | Partial | Verify Sticky Wilds adjust in size when reel height changes |
| PS-FEA-030 | P1 | Partial | Verify Sticky Wild behaviour when the reel height decreases on a later spin |
| PS-FEA-031 | P1 | Yes | Verify a reel fully covered by Sticky Wilds (7 rows) evaluates correctly |
| PS-FEA-032 | P1 | Yes | Verify at most 3 new Sticky Wilds land on a single Free Spin |
| PS-FEA-033 | P1 | Yes | Verify a new wild landing on a reel that already has a sticky is added without replacing the existing one |
| PS-FEA-034 | P2 | Partial | Verify wins involving sticky wilds highlight the wilds and show multiplied amount |
| PS-FEA-035 | P0 | Yes | Verify 0 to 6 Raining Wilds can appear on a Free Spin |
| PS-FEA-036 | P0 | Yes | Verify Raining Wilds do not persist to the next spin |
| PS-FEA-037 | P0 | Yes | Verify each Raining Wild shows its multiplier |
| PS-FEA-038 | P1 | No | Verify Raining Wild sizes |
| PS-FEA-039 | P1 | Yes | Verify Raining Wilds land only on reels 2-5 |
| PS-FEA-040 | P1 | Yes | Verify a Raining Wild replaces the underlying symbol and position is evaluated as Wild |
| PS-FEA-041 | P0 | Yes | Verify choosing Sticky Wilds starts Sticky Wilds FS and RGS logs choice |
| PS-FEA-042 | P0 | Yes | Verify choosing Raining Wilds starts Raining Wilds FS and RGS logs choice |
| PS-FEA-043 | P0 | Yes | Verify rapid double tap on both options only starts one feature |
| PS-FEA-044 | P0 | Yes | Verify refresh while choice screen is open returns to choice screen |
| PS-FEA-045 | P0 | Yes | Verify the choice screen shows correct spin counts for each BN count |
| PS-FEA-046 | P1 | Partial | Verify transition from base to FS and back preserves balance, bet and settings (sound, turbo) |
| PS-FEA-047 | P0 | Yes | Verify triggering spin pays line wins before entering FS |
| PS-FEA-048 | P0 | Yes | Verify which FS type is awarded for a bought feature |
| PS-FEA-049 | P0 | Yes | Verify a bought feature always lands at least 3 BN on the triggering spin |
| PS-FEA-050 | P0 | Yes | Verify double tapping Confirm debits only once |
| PS-FEA-051 | P0 | Yes | Verify refresh immediately after Buy confirm recovers the purchased feature |
| PS-FEA-052 | P1 | Yes | Verify Buy Feature not available while Auto Spin active |
| PS-FEA-053 | P1 | Partial | Verify bet adjustments inside the Buy interface update the cost live |
| PS-FEA-054 | P0 | Yes | Verify closing the browser mid-FS and relaunching restores the feature |
| PS-FEA-055 | P1 | Partial | Verify an unfinished feature resumes on another device for the same player |
| PS-FEA-056 | P0 | No | Verify behaviour of an unfinished feature left for 7+ days |
| PS-FEA-057 | P1 | No | Verify unfinished feature is restored after 6 days 23 hours inactivity |
| PS-FEA-058 | P0 | Yes | Verify network drop during FS spin request is recovered without spin loss |
| PS-FEA-059 | P0 | Yes | Verify refresh on FS summary screen does not credit twice |
