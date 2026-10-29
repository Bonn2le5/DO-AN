# BRIEFING — 2026-10-14T08:48:00Z

## Mission
Perform objective review and adversarial challenge of Milestone 2 (VNPay Sandbox Deposit Payment & Table Concurrency Control). Verify VNPay 2.1.0 implementation, HMAC checksum calculation/verification, 5-stage IPN validation (00/01/02/04/97), dual routing, table release on failure, run tests, and check integrity. Issue verdict.

## 🔒 My Identity
- Archetype: reviewer_critic
- Roles: reviewer, critic
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m2_1
- Original parent: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Milestone: Milestone 2 (VNPay Sandbox Deposit Payment & Table Concurrency Control)
- Instance: 1 of 1

## 🔒 Key Constraints
- Review-only — do NOT modify implementation code
- Check for integrity violations (hardcoded values, fake logic, test bypasses)
- Issue verdict APPROVE or REQUEST_CHANGES with actionable evidence

## Current Parent
- Conversation ID: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Updated: not yet

## Review Scope
- **Files to review**:
  - `moc-backend/config/settings.py`
  - `moc-backend/payments/models.py`
  - `moc-backend/payments/services.py`
  - `moc-backend/payments/serializers.py`
  - `moc-backend/payments/views.py`
  - `moc-backend/payments/urls.py`
  - `moc-backend/api/urls.py`
  - `moc-backend/reservations/services.py`
  - `moc-backend/reservations/views.py`
  - `moc-backend/foods/services.py`
  - `tests/e2e/test_milestone2_verification.py`
  - `tests/e2e/runner.py`
- **Interface contracts**: `.agents/teamwork/ORIGINAL_REQUEST.md`, `.agents/teamwork/teamwork_preview_orchestrator_gen2/PROJECT.md`
- **Review criteria**: Correctness, VNPay 2.1.0 spec adherence, HMAC-SHA512 integrity, IPN validation sequence (00/01/02/04/97), concurrency handling & table release, dual route endpoints, test coverage & validity.

## Review Checklist
- **Items reviewed**:
  - VNPay 2.1.0 HMAC calculation & verification: PASS (spec-compliant, matches oracle).
  - Dual Route endpoints (VN & EN): PASS (resolved correctly in Django router).
  - Refund Policy calculation (>24h, 6-24h, <6h, no-show) & PhieuHoanTien model: PASS.
  - Phase 1 Redis Hold (`giu_ban_tam_thoi`): PASS (SET NX EX 600, HTTP 409 BAN_DANG_BAN).
  - Phase 2 Table Concurrency (`tao_dat_ban`): FAIL (Critical defect in transaction scoping).
  - BOM Inventory Deduction (`khau_tru_nguyen_lieu_bom`): FAIL (Critical defect in transaction scoping).
  - IPN Webhook State Mutation (`process_ipn`): FAIL (Stages 3-5 un-scoped, lock released prematurely).
  - Test Suite Coverage: FAIL (Mocking `transaction.atomic` masked defects, zero tests for `tao_dat_ban`).
- **Verdict**: REQUEST_CHANGES
- **Unverified claims**: Worker claimed Phase 2 `select_for_update()` mutex was fully verified, but `tao_dat_ban` had 0% test coverage and is broken by `TransactionManagementError`.

## Attack Surface
- **Hypotheses tested**:
  - `select_for_update` execution outside `transaction.atomic`: CONFIRMED VULNERABLE (`TransactionManagementError` in autocommit mode).
  - Concurrent IPN webhook race condition: CONFIRMED VULNERABLE (Stages 3-5 outside lock).
  - Customer self-setting `is_no_show`: CONFIRMED VULNERABLE (Unrestricted parameter in `huy_dat_ban`).
- **Vulnerabilities found**:
  - CRITICAL: Broken transaction indentation in `tao_dat_ban`, `khau_tru_nguyen_lieu_bom`, `hoan_tra_nguyen_lieu_bom`, `process_ipn`, and `doi_trang_thai`.
  - MAJOR: Self-certifying tests with excessive mocking masking transaction errors and missing Phase 2 tests.
- **Untested angles**:
  - Live Redis TCP concurrency test (blocked in macOS sandbox, verified via logic and locmem).

## Key Decisions Made
- Issue explicit verdict: REQUEST_CHANGES. Provide precise line numbers and fix instructions.

## Artifact Index
- `.agents/teamwork/teamwork_preview_reviewer_m2_1/DISPATCH.md` — Dispatch instructions
- `.agents/teamwork/teamwork_preview_reviewer_m2_1/BRIEFING.md` — Situational awareness
- `.agents/teamwork/teamwork_preview_reviewer_m2_1/progress.md` — Liveness tracking
- `.agents/teamwork/teamwork_preview_reviewer_m2_1/handoff.md` — Final review and challenge report
