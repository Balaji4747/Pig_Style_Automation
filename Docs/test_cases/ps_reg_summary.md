# Regression Suite - Summary

Columns exactly as found in workbook: ['Test Case ID', 'Module', 'Feature', 'Sub-Feature', 'Test Scenario', 'Preconditions', 'Test Data', 'Detailed Test Steps', 'Expected Result', 'Actual Result', 'Priority', 'Severity', 'Test Type', 'Automation Candidate', 'Environment', 'Browser/Device', 'Status', 'Defect ID', 'Remarks']

Total data rows: 162

## Priority x Automation Candidate breakdown

| Priority | Automation Candidate | Count |
|---|---|---|
| P0 | Yes | 15 |
| P1 | No | 2 |
| P1 | Partial | 2 |
| P1 | Yes | 115 |
| P2 | No | 3 |
| P2 | Partial | 3 |
| P2 | Yes | 22 |

## Full row list (ID | Priority | Automation Candidate | Scenario)

| Test Case ID | Priority | Automation Candidate | Test Scenario |
|---|---|---|---|
| PS-REG-001 | P0 | Yes | Verify the game launches from the operator lobby in real-money mode and lands on the base game with correct initial state |
| PS-REG-002 | P0 | Yes | Verify the base game shows 6 reels and each reel displays between 2 and 7 symbols per spin |
| PS-REG-003 | P2 | Yes | Verify the ways-to-win counter equals the product of the symbol counts on all 6 reels |
| PS-REG-004 | P0 | Yes | Verify pressing the Play button starts exactly one game round at the selected bet |
| PS-REG-005 | P2 | Yes | Verify the increase control is disabled at maximum bet and decrease control disabled at minimum bet |
| PS-REG-006 | P2 | Yes | Verify bet controls are disabled while reels are spinning and during win presentation |
| PS-REG-007 | P2 | Yes | Verify bet cannot be changed during Free Spins |
| PS-REG-008 | P0 | Yes | Verify the balance is debited by exactly the bet amount once per paid spin |
| PS-REG-009 | P0 | Yes | Verify a base game win is credited to the balance and shown in the win field |
| PS-REG-010 | P1 | Yes | Verify displayed balance matches the wallet balance after each round |
| PS-REG-011 | P2 | Yes | Verify paytable values for symbol AA for 3, 4, 5 and 6 of a kind at the current bet |
| PS-REG-012 | P2 | Yes | Verify all paytable values scale linearly when bet changes |
| PS-REG-013 | P2 | No | Verify paytable content describes Wild, Bonus, both Free Spins options, Buy Free Spins and Megaways mechanics consistent with game behaviour |
| PS-REG-014 | P1 | Yes | Verify wins pay only for matching symbols on adjacent reels starting from reel 1 |
| PS-REG-015 | P1 | Yes | Verify a combination stops at the first reel without the symbol (or substituting Wild) |
| PS-REG-016 | P1 | Yes | Verify a win is multiplied by the number of ways (count of symbol on each contributing reel) |
| PS-REG-017 | P1 | Yes | Verify 2 matching symbols from reel 1 do not pay for any symbol |
| PS-REG-018 | P1 | Yes | Verify multiple different symbol wins in one spin are summed |
| PS-REG-019 | P1 | Yes | Verify only the longest combination for a given symbol/way is paid (no double pay of 3oak inside a 4oak) |
| PS-REG-020 | P1 | Yes | Verify Wild symbols can appear in the base game only on reels 2, 3, 4 and 5 |
| PS-REG-021 | P1 | Yes | Verify Wild substitutes for all paying symbols to complete a combination |
| PS-REG-022 | P1 | Yes | Verify Wild does not substitute for the Bonus symbol |
| PS-REG-023 | P1 | Yes | Verify base game Wild multipliers are applied to the way they participate in |
| PS-REG-024 | P0 | Yes | Verify 3 Bonus symbols anywhere on the reels trigger Free Spins |
| PS-REG-025 | P1 | Yes | Verify 2 Bonus symbols do not trigger Free Spins |
| PS-REG-026 | P0 | Yes | Verify the player can choose Sticky Wilds Free Spins or Raining Wilds Free Spins after trigger |
| PS-REG-027 | P1 | Yes | Verify Free Spins are played at the same bet as the triggering spin and no bet is debited per Free Spin |
| PS-REG-028 | P1 | Yes | Verify selecting Buy Feature opens the Buy Feature interface showing cost and available settings |
| PS-REG-029 | P1 | Yes | Verify Buy cost is exactly 100x the total bet for every bet level |
| PS-REG-030 | P0 | Yes | Verify confirming the purchase debits 100x bet once and starts the feature-triggering spin |
| PS-REG-031 | P1 | Yes | Verify Buy Feature is disabled or rejected when balance is below 100x bet |
| PS-REG-032 | P1 | Yes | Verify Buy Feature is hidden in jurisdictions where it is not permitted |
| PS-REG-033 | P2 | Yes | Verify Turbo Spin does not change results, wins or balance |
| PS-REG-034 | P0 | Yes | Verify Auto Spin plays exactly the selected number of spins and then stops |
| PS-REG-035 | P2 | Yes | Verify pressing Stop ends Auto Spin after the current round completes |
| PS-REG-036 | P2 | Yes | Verify Auto Spin stops when the selected spend limit is reached |
| PS-REG-037 | P2 | Yes | Verify Auto Spin stops when balance is insufficient for the next spin |
| PS-REG-038 | P2 | No | Verify the RTP values in game rules match the certified math |
| PS-REG-039 | P2 | No | Verify maximum win statement shows a concrete value consistent with configured cap |
| PS-REG-040 | P0 | Yes | Verify total game RTP from a large simulation matches the math file |
| PS-REG-041 | P1 | Yes | Verify deployed reel strips for BG1-BG9, FG1, FG2, Buy FG1, Buy FG2 match math file exactly |
| PS-REG-042 | P1 | Yes | Verify win amount for AA 6 OAK single way |
| PS-REG-043 | P1 | Yes | Verify win amount for BB 5 OAK with 2 on R3 |
| PS-REG-044 | P1 | Yes | Verify win amount for DD 3 OAK, ways 2x2x2 |
| PS-REG-045 | P1 | Yes | Verify wild multiplier win calculation: Base: single WC x2 |
| PS-REG-046 | P1 | Yes | Verify wild multiplier win calculation: Base: single WC x3 |
| PS-REG-047 | P1 | Yes | Verify wild multiplier win calculation: Base: two WC on same way |
| PS-REG-048 | P1 | Yes | Verify wild multiplier win calculation: Base: WC and symbol on same reel |
| PS-REG-049 | P1 | Yes | Verify wild multiplier win calculation: Base: WC x1 |
| PS-REG-050 | P1 | Yes | Verify FS win formula with Sticky/Raining Wilds: Win = (Bet x Pay/20) x product of wild multipliers |
| PS-REG-051 | P1 | Yes | Verify FS win with multiple ways where wilds participate in some ways only |
| PS-REG-052 | P1 | Yes | Verify 3 Bonus symbols award 7 Free Spins when Sticky Wilds is chosen |
| PS-REG-053 | P1 | Yes | Verify 6 Bonus symbols award 20 Free Spins when Sticky Wilds is chosen |
| PS-REG-054 | P1 | Yes | Verify 3 Bonus symbols award 15 Free Spins when Raining Wilds is chosen |
| PS-REG-055 | P1 | Yes | Verify 6 Bonus symbols award 30 Free Spins when Raining Wilds is chosen |
| PS-REG-056 | P1 | Yes | Verify a forced outcome exceeding the max win cap is credited at exactly the cap and the feature ends |
| PS-REG-057 | P1 | Yes | Verify cap applies to base game single spin win |
| PS-REG-058 | P1 | Yes | Verify minimum trigger (3 BN) starts Sticky Wilds FS with 7 spins |
| PS-REG-059 | P1 | Yes | Verify maximum trigger (6 BN) starts Sticky Wilds FS with 20 spins |
| PS-REG-060 | P0 | Yes | Verify Sticky Wilds FS ends after the last spin and shows total feature win, then returns to base game |
| PS-REG-061 | P1 | Yes | Verify Bonus symbols do not appear and feature cannot retrigger in Sticky Wilds FS |
| PS-REG-062 | P1 | Yes | Verify Sticky Wilds FS plays at trigger bet with no per-spin debit |
| PS-REG-063 | P1 | Yes | Verify total win meter accumulates each spin win during Sticky Wilds FS |
| PS-REG-064 | P1 | Yes | Verify when Sticky Wilds FS winnings reach the player balance |
| PS-REG-065 | P1 | Yes | Verify Sticky Wilds FS resumes after browser refresh with same remaining spins, wilds and total win |
| PS-REG-066 | P1 | Yes | Verify refresh while a Sticky Wilds FS spin is animating restores the already-determined result |
| PS-REG-067 | P1 | Yes | Verify reaching max win cap during Sticky Wilds FS ends the feature immediately |
| PS-REG-068 | P1 | Yes | Verify minimum trigger (3 BN) starts Raining Wilds FS with 15 spins |
| PS-REG-069 | P1 | Yes | Verify maximum trigger (6 BN) starts Raining Wilds FS with 30 spins |
| PS-REG-070 | P0 | Yes | Verify Raining Wilds FS ends after the last spin and shows total feature win, then returns to base game |
| PS-REG-071 | P1 | Yes | Verify Bonus symbols do not appear and feature cannot retrigger in Raining Wilds FS |
| PS-REG-072 | P1 | Yes | Verify Raining Wilds FS plays at trigger bet with no per-spin debit |
| PS-REG-073 | P1 | Yes | Verify total win meter accumulates each spin win during Raining Wilds FS |
| PS-REG-074 | P1 | Yes | Verify when Raining Wilds FS winnings reach the player balance |
| PS-REG-075 | P1 | Yes | Verify Raining Wilds FS resumes after browser refresh with same remaining spins, wilds and total win |
| PS-REG-076 | P1 | Yes | Verify refresh while a Raining Wilds FS spin is animating restores the already-determined result |
| PS-REG-077 | P1 | Yes | Verify reaching max win cap during Raining Wilds FS ends the feature immediately |
| PS-REG-078 | P1 | Yes | Verify a Sticky Wild remains in its reel for all remaining Free Spins |
| PS-REG-079 | P1 | Yes | Verify a Sticky Wild keeps its assigned multiplier for the rest of the feature |
| PS-REG-080 | P1 | Yes | Verify each landing Sticky Wild shows its assigned multiplier |
| PS-REG-081 | P1 | Yes | Verify 0 to 6 Raining Wilds can appear on a Free Spin |
| PS-REG-082 | P1 | Yes | Verify Raining Wilds do not persist to the next spin |
| PS-REG-083 | P1 | Yes | Verify each Raining Wild shows its multiplier |
| PS-REG-084 | P1 | Yes | Verify choosing Sticky Wilds starts Sticky Wilds FS and RGS logs choice |
| PS-REG-085 | P1 | Yes | Verify choosing Raining Wilds starts Raining Wilds FS and RGS logs choice |
| PS-REG-086 | P1 | Yes | Verify rapid double tap on both options only starts one feature |
| PS-REG-087 | P1 | Yes | Verify refresh while choice screen is open returns to choice screen |
| PS-REG-088 | P1 | Yes | Verify the choice screen shows correct spin counts for each BN count |
| PS-REG-089 | P1 | Yes | Verify triggering spin pays line wins before entering FS |
| PS-REG-090 | P1 | Yes | Verify which FS type is awarded for a bought feature |
| PS-REG-091 | P1 | Yes | Verify a bought feature always lands at least 3 BN on the triggering spin |
| PS-REG-092 | P1 | Yes | Verify double tapping Confirm debits only once |
| PS-REG-093 | P1 | Yes | Verify refresh immediately after Buy confirm recovers the purchased feature |
| PS-REG-094 | P1 | Yes | Verify closing the browser mid-FS and relaunching restores the feature |
| PS-REG-095 | P1 | No | Verify behaviour of an unfinished feature left for 7+ days |
| PS-REG-096 | P1 | Yes | Verify network drop during FS spin request is recovered without spin loss |
| PS-REG-097 | P1 | Yes | Verify refresh on FS summary screen does not credit twice |
| PS-REG-098 | P1 | Yes | Verify spin is blocked when balance is 0.01 below the selected bet |
| PS-REG-099 | P1 | Yes | Verify game behaviour with zero balance on launch |
| PS-REG-100 | P2 | Yes | Verify Buy accepted when balance equals exactly 100x bet |
| PS-REG-101 | P2 | Yes | Verify win equal to the cap exactly is paid in full without truncation message error |
| PS-REG-102 | P2 | Yes | Verify win of cap + 0.01 is truncated to cap |
| PS-REG-103 | P1 | Yes | Verify spam clicking Play (10 clicks/sec for 3s) starts only sequential rounds |
| PS-REG-104 | P2 | Yes | Verify no template placeholders like {{text1}} appear anywhere |
| PS-REG-105 | P2 | Partial | Verify full smoke flow on Windows 11 with Chrome (latest, latest-1): load, spin, win, bet change, FS (both types), Buy, Auto Spin, Info, Sou |
| PS-REG-106 | P2 | Partial | Verify full smoke flow on iOS 17/18 iPhone with Safari: load, spin, win, bet change, FS (both types), Buy, Auto Spin, Info, Sound |
| PS-REG-107 | P2 | Partial | Verify full smoke flow on Android 13/14 phone with Chrome: load, spin, win, bet change, FS (both types), Buy, Auto Spin, Info, Sound |
| PS-REG-108 | P1 | Yes | Refresh: during base spin |
| PS-REG-109 | P1 | Yes | Refresh: during win presentation |
| PS-REG-110 | P0 | Yes | Refresh: during Free Spins |
| PS-REG-111 | P1 | Yes | Refresh: on FS choice screen |
| PS-REG-112 | P1 | Yes | Refresh: immediately after Buy confirm |
| PS-REG-113 | P1 | Yes | Close/reopen: during base spin |
| PS-REG-114 | P1 | Yes | Close/reopen: during FS |
| PS-REG-115 | P1 | Yes | Network loss: before spin request |
| PS-REG-116 | P1 | Yes | Network loss: after request sent, before response |
| PS-REG-117 | P1 | Yes | Network loss: during FS |
| PS-REG-118 | P1 | Yes | App background: iOS during spin |
| PS-REG-119 | P1 | Yes | App background: Android during FS |
| PS-REG-120 | P1 | Yes | Session expiration: mid FS |
| PS-REG-121 | P1 | Yes | Wallet credit failure: after win |
| PS-REG-122 | P1 | Yes | Wallet debit failure |
| PS-REG-123 | P1 | Yes | API timeout: spin |
| PS-REG-124 | P1 | Yes | Server 500: spin |
| PS-REG-125 | P1 | Yes | Reload: immediately after feature trigger |
| PS-REG-126 | P1 | Yes | Reload: during Sticky FS with 5 stickies |
| PS-REG-127 | P1 | Yes | Reload: during Raining FS mid-drop |
| PS-REG-128 | P1 | Yes | Reload: during max win |
| PS-REG-129 | P1 | Yes | Browser crash: during FS |
| PS-REG-130 | P1 | Yes | Duplicate prevention: resumed round |
| PS-REG-131 | P1 | Yes | Suspended state: resume point |
| PS-REG-132 | P0 | Yes | Bet transaction: single debit |
| PS-REG-133 | P0 | Yes | Win transaction: amount |
| PS-REG-134 | P1 | Yes | Zero win: closing call |
| PS-REG-135 | P1 | Yes | Buy transaction |
| PS-REG-136 | P1 | Yes | FS transactions |
| PS-REG-137 | P1 | Yes | Round lifecycle: FS in one round |
| PS-REG-138 | P1 | Yes | Idempotency: duplicate spin request |
| PS-REG-139 | P1 | Yes | Idempotency: duplicate credit |
| PS-REG-140 | P1 | Yes | Replay: old round request |
| PS-REG-141 | P1 | Yes | Sequence: out-of-order requests |
| PS-REG-142 | P1 | Yes | Sequence: spin during FS |
| PS-REG-143 | P1 | Yes | Tampered bet value |
| PS-REG-144 | P1 | Yes | Tampered bet above max |
| PS-REG-145 | P1 | Yes | Tampered buy cost |
| PS-REG-146 | P1 | Yes | Tampered FS choice |
| PS-REG-147 | P1 | Yes | Bet change mid-FS via API |
| PS-REG-148 | P1 | Yes | Session validation: invalid token |
| PS-REG-149 | P1 | Yes | Session validation: other player's round |
| PS-REG-150 | P1 | Partial | Reconciliation: bet/win totals |
| PS-REG-151 | P1 | Partial | Reconciliation: history vs RGS |
| PS-REG-152 | P1 | Yes | Balance consistency after errors |
| PS-REG-153 | P1 | No | RNG: outcome server-side |
| PS-REG-154 | P1 | Yes | Max win: transaction |
| PS-REG-155 | P2 | Yes | Insufficient balance: spin |
| PS-REG-156 | P2 | Yes | Insufficient balance: Buy |
| PS-REG-157 | P2 | Yes | Session error: expired |
| PS-REG-158 | P2 | Yes | Server error: 500 |
| PS-REG-159 | P2 | Yes | Timeout: spin |
| PS-REG-160 | P2 | Yes | Failed spin: RNG/engine error |
| PS-REG-161 | P2 | Yes | Failed transaction: debit rejected by wallet |
| PS-REG-162 | P2 | Yes | Recovery after error |
