# STR - Transaction Testing - Summary

Columns exactly as found in workbook: ['Test Case ID', 'Module', 'Feature', 'Sub-Feature', 'Test Scenario', 'Preconditions', 'Test Data', 'Detailed Test Steps', 'Expected Result', 'Actual Result', 'Priority', 'Severity', 'Test Type', 'Automation Candidate', 'Environment', 'Browser/Device', 'Status', 'Defect ID', 'Remarks']

Total data rows: 27

## Priority x Automation Candidate breakdown

| Priority | Automation Candidate | Count |
|---|---|---|
| P0 | No | 1 |
| P0 | Partial | 2 |
| P0 | Yes | 20 |
| P1 | Partial | 2 |
| P1 | Yes | 2 |

## Full row list (ID | Priority | Automation Candidate | Scenario)

| Test Case ID | Priority | Automation Candidate | Test Scenario |
|---|---|---|---|
| PS-STR-001 | P0 | Yes | Bet transaction: single debit |
| PS-STR-002 | P0 | Yes | Win transaction: amount |
| PS-STR-003 | P0 | Yes | Zero win: closing call |
| PS-STR-004 | P0 | Yes | Buy transaction |
| PS-STR-005 | P0 | Yes | FS transactions |
| PS-STR-006 | P0 | Yes | Round lifecycle: FS in one round |
| PS-STR-007 | P0 | Yes | Idempotency: duplicate spin request |
| PS-STR-008 | P0 | Yes | Idempotency: duplicate credit |
| PS-STR-009 | P0 | Yes | Replay: old round request |
| PS-STR-010 | P0 | Yes | Sequence: out-of-order requests |
| PS-STR-011 | P0 | Yes | Sequence: spin during FS |
| PS-STR-012 | P0 | Yes | Tampered bet value |
| PS-STR-013 | P0 | Yes | Tampered bet above max |
| PS-STR-014 | P0 | Yes | Tampered buy cost |
| PS-STR-015 | P0 | Yes | Tampered FS choice |
| PS-STR-016 | P0 | Yes | Bet change mid-FS via API |
| PS-STR-017 | P0 | Yes | Session validation: invalid token |
| PS-STR-018 | P0 | Yes | Session validation: other player's round |
| PS-STR-019 | P0 | Partial | Reconciliation: bet/win totals |
| PS-STR-020 | P0 | Partial | Reconciliation: history vs RGS |
| PS-STR-021 | P0 | Yes | Balance consistency after errors |
| PS-STR-022 | P0 | No | RNG: outcome server-side |
| PS-STR-023 | P0 | Yes | Max win: transaction |
| PS-STR-024 | P1 | Yes | Unexpected response: missing fields |
| PS-STR-025 | P1 | Yes | Unexpected response: negative win |
| PS-STR-026 | P1 | Partial | Responsible gaming: reality check |
| PS-STR-027 | P1 | Partial | Responsible gaming: session/loss limit |
