# BRIEFING — 2026-10-14T08:52:00Z

## Mission
Adversarial stress-testing and empirical challenge of Milestone 2: VNPay hash tampering, edge cases, IPN replay attacks, exact boundary refund calculations, PhieuHoanTien integrity, and 2-phase table concurrency control.

## 🔒 My Identity
- Archetype: empirical challenger
- Roles: critic, specialist
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m2_1
- Original parent: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Milestone: Milestone 2: VNPay Sandbox & Table Concurrency Control
- Instance: 1 of 1

## 🔒 Key Constraints
- Review-only — do NOT modify implementation code
- Report any failures as findings — do NOT fix them myself
- EMPIRICAL CHALLENGER: Must run verification code myself; write test harnesses in tests/, execute them, reproduce bugs empirically
- .agents/teamwork/ must contain only metadata — source, tests, or data there is a violation

## Current Parent
- Conversation ID: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Updated: 2026-10-14T08:39:23Z

## Review Scope
- **Files to review**:
  - `moc-backend/payments/services.py`
  - `moc-backend/payments/views.py`
  - `moc-backend/payments/models.py`
  - `moc-backend/payments/serializers.py`
  - `moc-backend/payments/urls.py`
  - `moc-backend/reservations/services.py`
  - `moc-backend/reservations/views.py`
  - `moc-backend/foods/services.py`
  - `moc-backend/orders/services.py`
- **Interface contracts**:
  - PROJECT.md Section 2: VNPay Sandbox Payment Contract (HMAC-SHA512, IPN 00/01/02/04/97, Return URL, Cancellation code 24)
  - PROJECT.md Section 1: Table Concurrency Control Contract (Phase 1 Redis SET NX EX 600, Phase 2 Pessimistic DB Lock)
  - PROJECT.md Section 2: Deposit Refund Policy (>24h 100%, 6-24h 50%, <6h 0%, No-show 0%)
- **Review criteria**: Robustness against hash tampering, injection, replay attacks, duplicate calls, boundary floating point precision, deadlock prevention, financial data integrity.

## Key Decisions Made
- Formulated verdict: **REQUEST_CHANGES** due to 6 empirically demonstrated critical and high bugs across VNPay IPN webhook permissions, QueryDict list checksum invalidation, premature transaction atomic exits, customer payment cancellation table deadlocks, and table hold endpoint RBAC restrictions.
- Created authoritative adversarial test suite `tests/e2e/test_adversarial_challenger_m2.py` (16 test cases, 100% reproducible).

## Artifact Index
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m2_1/DISPATCH.md` — Dispatch instructions and objectives
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m2_1/progress.md` — Liveness heartbeat & progress log
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m2_1/handoff.md` — Final adversarial verification report & verdict (REQUEST_CHANGES)
- `/Users/VuVan/Documents/DO-AN/tests/e2e/test_adversarial_challenger_m2.py` — Authoritative empirical challenger test suite

## Attack Surface
- **Hypotheses tested**:
  1. VNPay HMAC-SHA512 single-character tampering across all params and hashes -> Confirmed rejected (robust).
  2. Empty/None/Unicode Vietnamese parameters -> Confirmed identical to oracle (robust).
  3. QueryDict handling in `process_ipn` -> VULNERABILITY CONFIRMED: `dict(query_params)` retains list values, generating invalid checksums (97).
  4. Public access to IPN webhook and return endpoints -> VULNERABILITY CONFIRMED: returns HTTP 401 Unauthorized.
  5. IPN replay attack against confirmed order -> Correctly returns code 02 (robust).
  6. Atomic lock scope in `process_ipn` -> VULNERABILITY CONFIRMED: `transaction.atomic()` exits prematurely before idempotency check and state mutation.
  7. Customer cancellation (code 24) table release -> VULNERABILITY CONFIRMED: `dat_ban.trang_thai` remains `cho_thanh_toan` in DB, permanently locking table.
  8. Exact boundary float calculations for refund policy (24.00000001h, 24.0h, 6.0h, 5.99999h, 0.0h, negative, no-show) -> 100% mathematically correct across 500 randomized trials (robust).
  9. Table hold permissions on `/api/tables/{id}/giu_ban/` -> VULNERABILITY CONFIRMED: returns 401 for anonymous and 403 for customers.
  10. Atomic lock scope in `tao_dat_ban` and `khau_tru_nguyen_lieu_bom` -> VULNERABILITY CONFIRMED: `transaction.atomic()` exits prematurely before `select_for_update()` and updates.
- **Vulnerabilities found**: 6 confirmed vulnerabilities (2 Critical, 4 High).
- **Untested angles**: None within Milestone 2 scope.

## Loaded Skills
- None specified
