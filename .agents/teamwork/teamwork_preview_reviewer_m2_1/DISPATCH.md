# Dispatch: m2_reviewer_1

## Task
You are Reviewer 1 for Milestone 2: VNPay Sandbox Deposit Payment & Table Concurrency Control.

## Working Directory
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m2_1`

## MANDATORY READ
- Read `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- Read `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen2/PROJECT.md`
- Read `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m2_1/handoff.md`

## Review Objectives
1. Inspect `moc-backend/config/settings.py`, `moc-backend/payments/` (models, services, serializers, views, urls), and `moc-backend/api/urls.py`.
2. Verify VNPay 2.1.0 implementation:
   - Parameter collation and sorting (ASCII alphabetical order).
   - HMAC-SHA512 checksum creation and verification matching `vnpay_oracle.py`.
   - 5-stage IPN webhook validation (Stage 1 checksum -> 97, Stage 2 order -> 01, Stage 3 amount -> 04, Stage 4 idempotency -> 02, Stage 5 state mutation -> 00, failure code 24 -> table release).
   - Dual routing `/api/payments/vnpay/...` and `/api/thanh-toan/vnpay/...`, including frontend session adapter `/api/thanh-toan/vnpay/tao-phien/`.
3. Run verification commands:
   - `./moc-backend/.venv/bin/python moc-backend/manage.py check`
   - `./moc-backend/.venv/bin/python tests/e2e/runner.py`
   - `./moc-backend/.venv/bin/python tests/e2e/test_milestone2_verification.py`
4. Formulate explicit verdict: **APPROVE** or **REQUEST_CHANGES**.

Write your handoff report to `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m2_1/handoff.md` and notify caller when done.


## 2026-10-14T08:39:23Z
Sender: 3b4ac039-b543-49a4-9b3d-21e996771d3e
Priority: MESSAGE_PRIORITY_HIGH
Content:
You are m2_reviewer_1, Reviewer 1 for Milestone 2.
Your working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m2_1
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m2_1/DISPATCH.md
MANDATORY: Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m2_1/handoff.md.
Review VNPay 2.1.0 implementation, HMAC checksum, IPN validation 00/01/02/04/97, and dual route endpoints. Run builds and tests.
Deliver your review report and verdict (APPROVE or REQUEST_CHANGES) in /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m2_1/handoff.md and notify the caller.
