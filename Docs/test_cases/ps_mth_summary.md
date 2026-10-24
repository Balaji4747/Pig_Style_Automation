# Math Validation - Summary

Columns exactly as found in workbook: ['Test Case ID', 'Module', 'Feature', 'Sub-Feature', 'Test Scenario', 'Preconditions', 'Test Data', 'Detailed Test Steps', 'Expected Result', 'Actual Result', 'Priority', 'Severity', 'Test Type', 'Automation Candidate', 'Environment', 'Browser/Device', 'Status', 'Defect ID', 'Remarks']

Total data rows: 63

## Priority x Automation Candidate breakdown

| Priority | Automation Candidate | Count |
|---|---|---|
| P0 | No | 4 |
| P0 | Yes | 41 |
| P1 | No | 1 |
| P1 | Yes | 9 |
| P2 | No | 1 |
| P2 | Yes | 7 |

## Full row list (ID | Priority | Automation Candidate | Scenario)

| Test Case ID | Priority | Automation Candidate | Test Scenario |
|---|---|---|---|
| PS-MTH-001 | P0 | Yes | Verify total game RTP from a large simulation matches the math file |
| PS-MTH-002 | P0 | Yes | Verify base game (non-FS) RTP contribution |
| PS-MTH-003 | P0 | Yes | Verify Free Spins RTP contribution |
| PS-MTH-004 | P0 | Yes | Verify RTP of Sticky Wilds FS and Raining Wilds FS when chosen at natural trigger |
| PS-MTH-005 | P0 | Yes | Verify RTP of Buy Feature for FG1 (Raining Wilds: 15/18/25/30 FS) |
| PS-MTH-006 | P0 | Yes | Verify RTP of Buy Feature for FG2 (Sticky Wilds: 7/12/15/20 FS) |
| PS-MTH-007 | P1 | No | Verify Buy Feature RTP is not lower than base game RTP where jurisdiction requires |
| PS-MTH-008 | P1 | Yes | Verify hit frequency of winning base rounds |
| PS-MTH-009 | P2 | Yes | Verify hit frequency of bought features |
| PS-MTH-010 | P2 | Yes | Verify volatility index / SD from simulation |
| PS-MTH-011 | P0 | Yes | Verify base game Free Spins trigger frequency |
| PS-MTH-012 | P1 | Yes | Verify only reel sets BG1 and BG6 can produce a Free Spins trigger |
| PS-MTH-013 | P1 | Yes | Verify base game reel set selection frequencies |
| PS-MTH-014 | P0 | Yes | Verify deployed reel strips for BG1-BG9, FG1, FG2, Buy FG1, Buy FG2 match math file exactly |
| PS-MTH-015 | P1 | Yes | Verify per-reel height distribution (2..7) matches configured weights |
| PS-MTH-016 | P1 | Yes | Verify ways = product of reel heights for all spins in simulation |
| PS-MTH-017 | P0 | Yes | Verify win amount for AA 6 OAK single way |
| PS-MTH-018 | P0 | Yes | Verify win amount for BB 5 OAK with 2 on R3 |
| PS-MTH-019 | P0 | Yes | Verify win amount for CC 4 OAK, bet 0.20 |
| PS-MTH-020 | P0 | Yes | Verify win amount for DD 3 OAK, ways 2x2x2 |
| PS-MTH-021 | P0 | Yes | Verify win amount for EE 6 OAK |
| PS-MTH-022 | P0 | Yes | Verify win amount for FF 4 OAK |
| PS-MTH-023 | P0 | Yes | Verify win amount for GG/HH/JJ 5 OAK |
| PS-MTH-024 | P0 | Yes | Verify win amount for LL 3 OAK minimum pay |
| PS-MTH-025 | P0 | Yes | Verify win amount for KK 3 OAK at min bet rounding |
| PS-MTH-026 | P1 | Yes | Verify rounding rule for wins that are not whole currency units |
| PS-MTH-027 | P0 | Yes | Verify wild multiplier win calculation: Base: single WC x2 |
| PS-MTH-028 | P0 | Yes | Verify wild multiplier win calculation: Base: single WC x3 |
| PS-MTH-029 | P0 | Yes | Verify wild multiplier win calculation: Base: two WC on same way |
| PS-MTH-030 | P0 | Yes | Verify wild multiplier win calculation: Base: WC and symbol on same reel |
| PS-MTH-031 | P0 | Yes | Verify wild multiplier win calculation: Base: WC x1 |
| PS-MTH-032 | P1 | Yes | Verify base game Wild multiplier distribution |
| PS-MTH-033 | P0 | Yes | Verify Raining Wilds multiplier distribution |
| PS-MTH-034 | P0 | Yes | Verify Sticky Wilds multiplier distribution |
| PS-MTH-035 | P1 | Yes | Verify Buy FG2 Sticky Wild multiplier distribution |
| PS-MTH-036 | P0 | Yes | Verify FS win formula with Sticky/Raining Wilds: Win = (Bet x Pay/20) x product of wild multipliers |
| PS-MTH-037 | P0 | Yes | Verify FS win with multiple ways where wilds participate in some ways only |
| PS-MTH-038 | P0 | Yes | Verify 3 Bonus symbols award 7 Free Spins when Sticky Wilds is chosen |
| PS-MTH-039 | P0 | Yes | Verify 4 Bonus symbols award 12 Free Spins when Sticky Wilds is chosen |
| PS-MTH-040 | P0 | Yes | Verify 5 Bonus symbols award 15 Free Spins when Sticky Wilds is chosen |
| PS-MTH-041 | P0 | Yes | Verify 6 Bonus symbols award 20 Free Spins when Sticky Wilds is chosen |
| PS-MTH-042 | P0 | Yes | Verify 3 Bonus symbols award 15 Free Spins when Raining Wilds is chosen |
| PS-MTH-043 | P0 | Yes | Verify 4 Bonus symbols award 18 Free Spins when Raining Wilds is chosen |
| PS-MTH-044 | P0 | Yes | Verify 5 Bonus symbols award 25 Free Spins when Raining Wilds is chosen |
| PS-MTH-045 | P0 | Yes | Verify 6 Bonus symbols award 30 Free Spins when Raining Wilds is chosen |
| PS-MTH-046 | P2 | Yes | Verify average number of Free Spins per trigger |
| PS-MTH-047 | P2 | Yes | Verify distribution of Bonus symbol count (3/4/5/6) on triggering spins |
| PS-MTH-048 | P0 | Yes | Verify number of Raining Wilds per FG1 spin follows math weights |
| PS-MTH-049 | P0 | Yes | Verify Raining Wilds are placed only on reels 2-5 |
| PS-MTH-050 | P0 | Yes | Verify number of new Sticky Wilds per FG2 spin follows math weights |
| PS-MTH-051 | P1 | Yes | Verify reel height distribution conditional on number of sticky wilds on a reel |
| PS-MTH-052 | P2 | Yes | Verify average number of Sticky Wilds at end of FG2 |
| PS-MTH-053 | P0 | No | Verify maximum exposure of base game + FS |
| PS-MTH-054 | P0 | No | Verify maximum exposure of bought features |
| PS-MTH-055 | P0 | Yes | Verify a forced outcome exceeding the max win cap is credited at exactly the cap and the feature ends |
| PS-MTH-056 | P0 | Yes | Verify cap applies to base game single spin win |
| PS-MTH-057 | P0 | Yes | Verify server evaluates wins with bet denominator 20 (math 'Number of Lines Played: 20') |
| PS-MTH-058 | P0 | No | Verify configured min and max bet match approved values |
| PS-MTH-059 | P2 | Yes | Verify expected return per buy |
| PS-MTH-060 | P2 | Yes | Verify Buy RTP base-game component (triggering spin wins) |
| PS-MTH-061 | P0 | No | Verify the math file supplied is the correct version for Pig Style |
| PS-MTH-062 | P0 | Yes | Verify Bonus symbol cannot appear during Free Spins |
| PS-MTH-063 | P2 | No | Verify Wilds in FS come only from feature placement (FS reel strips contain no WC) |
