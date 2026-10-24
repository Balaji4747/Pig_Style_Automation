# Edge & Boundary Cases - Summary

Columns exactly as found in workbook: ['Test Case ID', 'Module', 'Feature', 'Sub-Feature', 'Test Scenario', 'Preconditions', 'Test Data', 'Detailed Test Steps', 'Expected Result', 'Actual Result', 'Priority', 'Severity', 'Test Type', 'Automation Candidate', 'Environment', 'Browser/Device', 'Status', 'Defect ID', 'Remarks']

Total data rows: 42

## Priority x Automation Candidate breakdown

| Priority | Automation Candidate | Count |
|---|---|---|
| P0 | Yes | 16 |
| P1 | Yes | 17 |
| P2 | No | 1 |
| P2 | Yes | 6 |
| P3 | No | 1 |
| P3 | Yes | 1 |

## Full row list (ID | Priority | Automation Candidate | Scenario)

| Test Case ID | Priority | Automation Candidate | Test Scenario |
|---|---|---|---|
| PS-EDG-001 | P0 | Yes | Verify spin is accepted at minimum bet when balance equals exactly the minimum bet and balance becomes 0.00 on loss |
| PS-EDG-002 | P0 | Yes | Verify spin at maximum bet with balance exactly equal to max bet |
| PS-EDG-003 | P0 | Yes | Verify spin is blocked when balance is 0.01 below the selected bet |
| PS-EDG-004 | P0 | Yes | Verify game behaviour with zero balance on launch |
| PS-EDG-005 | P1 | Yes | Verify player can lower bet to continue playing when balance below current bet |
| PS-EDG-006 | P0 | Yes | Verify Buy accepted when balance equals exactly 100x bet |
| PS-EDG-007 | P1 | Yes | Verify Buy at minimum bet costs 100 x min bet |
| PS-EDG-008 | P1 | Yes | Verify Buy at maximum bet and display of large cost |
| PS-EDG-009 | P0 | Yes | Verify display of a large win (>= 10,000x bet) with full digits and separators |
| PS-EDG-010 | P0 | Yes | Verify win equal to the cap exactly is paid in full without truncation message error |
| PS-EDG-011 | P0 | Yes | Verify win of cap + 0.01 is truncated to cap |
| PS-EDG-012 | P1 | Yes | Verify base spin hitting cap while also landing 3 BN |
| PS-EDG-013 | P1 | Yes | Verify a spin with wins on 5+ symbols and thousands of ways evaluates and presents correctly |
| PS-EDG-014 | P1 | Yes | Verify 117,649 ways of AA 6oak with no wilds |
| PS-EDG-015 | P0 | Yes | Verify extreme multiplier product in Sticky FS (e.g. 28 stickies x3) is computed without overflow |
| PS-EDG-016 | P2 | Yes | Verify 3 BN trigger when reels are at 7 rows |
| PS-EDG-017 | P2 | Yes | Verify 6 BN trigger with all reels at 2 rows |
| PS-EDG-018 | P2 | No | Verify whether two Bonus symbols can appear on one reel |
| PS-EDG-019 | P0 | Yes | Verify spam clicking Play (10 clicks/sec for 3s) starts only sequential rounds |
| PS-EDG-020 | P1 | Yes | Verify pressing space and clicking Play simultaneously starts one round |
| PS-EDG-021 | P1 | Yes | Verify clicking Play during win presentation skips presentation and starts next round only once |
| PS-EDG-022 | P1 | Yes | Verify inputs during FS intro/outro transitions are ignored |
| PS-EDG-023 | P1 | Yes | Verify Buy button disabled while reels spin |
| PS-EDG-024 | P1 | Yes | Verify Auto Spin stops exactly when spend limit equals cumulative stake |
| PS-EDG-025 | P2 | Yes | Verify the smallest and largest auto spin count options |
| PS-EDG-026 | P1 | Yes | Verify FS triggered on the last auto spin completes and Auto Spin ends after |
| PS-EDG-027 | P1 | Yes | Verify Stop pressed during auto-triggered FS |
| PS-EDG-028 | P0 | Yes | Verify refresh during the last Free Spin |
| PS-EDG-029 | P0 | Yes | Verify refresh immediately after 3 BN land (before choice) |
| PS-EDG-030 | P0 | Yes | Verify spin with expired session token |
| PS-EDG-031 | P0 | Yes | Verify session timeout during FS |
| PS-EDG-032 | P1 | Yes | Verify UI behaviour with 10s server latency on spin |
| PS-EDG-033 | P0 | Yes | Verify late response after client timeout is reconciled |
| PS-EDG-034 | P1 | Yes | Verify browser back during spin |
| PS-EDG-035 | P1 | Yes | Verify back then forward during FS |
| PS-EDG-036 | P0 | Yes | Verify same game opened in two tabs for one session |
| PS-EDG-037 | P2 | Yes | Verify currency with 0 decimals and with 3 decimals display |
| PS-EDG-038 | P2 | Yes | Verify balance display with 7+ digits |
| PS-EDG-039 | P3 | Yes | Verify history with many rounds (paging) |
| PS-EDG-040 | P2 | Yes | Verify FS spin with all reels at 7 rows and sticky wilds |
| PS-EDG-041 | P1 | Yes | Verify changing bet and immediately pressing Play uses the new bet |
| PS-EDG-042 | P3 | No | Verify retention of persistent game data up to 90 days |
