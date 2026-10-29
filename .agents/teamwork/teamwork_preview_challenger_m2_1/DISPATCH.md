# Dispatch: m2_challenger_1

## Task
You are Challenger 1 for Milestone 2: Adversarial VNPay & Refund Verification.

## Working Directory
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m2_1`

## MANDATORY READ
- Read `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- Read `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen2/PROJECT.md`
- Read `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m2_1/handoff.md`

## Challenge Objectives
1. Empirically verify VNPay 2.1.0 security and robustness:
   - HMAC-SHA512 checksum tampering (altering 1 character in params or hash must yield False / 97).
   - Empty/None parameter handling, special characters, unicode Vietnamese diacritics.
   - IPN replay attacks, malformed amount parameters, duplicate calls to terminal orders (idempotency 02).
   - Customer payment cancellation (code 24) releasing table hold.
2. Empirically verify Deposit Cancellation & Refund policies:
   - Precise boundary testing: delta_hours = 24.00000001 (100%), 24.0 (50%), 6.0 (50%), 5.99999 (0%), 0.0 (0%), negative / no-show (0%).
   - `PhieuHoanTien` integrity: unique code, customer info, branch info, financial breakdown.
3. Write an adversarial stress test script and execute it.
4. Formulate explicit verdict: **APPROVE** or **REQUEST_CHANGES**.

Write your handoff report to `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m2_1/handoff.md` and notify caller when done.


## 2026-10-14T08:39:23Z
You are m2_challenger_1, Challenger 1 for Milestone 2.
Your working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m2_1
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m2_1/DISPATCH.md
MANDATORY: Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m2_1/handoff.md.
Stress test VNPay hash tampering, edge cases, IPN replay attacks, and exact boundary refund calculations. Run adversarial tests.
Deliver your report and verdict (APPROVE or REQUEST_CHANGES) in /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m2_1/handoff.md and notify the caller.
