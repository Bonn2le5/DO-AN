# BRIEFING — 2026-10-14T08:48:00Z

## Mission
Independently review and stress-test Milestone 2 implementations: 2-Phase Concurrency Control (Phase 1 Redis hold HTTP 409, Phase 2 select_for_update table mutex), BOM Material Deduction with deadlock prevention (sorted IDs), and Deposit Refund Policy / PhieuHoanTien. Run independent verification tests and provide an objective verdict.

## 🔒 My Identity
- Archetype: reviewer
- Roles: reviewer, critic
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m2_2
- Original parent: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Milestone: Milestone 2 (2-Phase Concurrency Control, BOM Deduction & Refund Policy)
- Instance: 2 of 2

## 🔒 Key Constraints
- Review-only — do NOT modify implementation code.
- Actively check for integrity violations: hardcoded test results, dummy/facade implementations, shortcuts bypassing core logic, fabricated verification outputs.
- Must execute independent test suites and builds.
- Issue explicit verdict: APPROVE or REQUEST_CHANGES.
- Deliver handoff report to `.agents/teamwork/teamwork_preview_reviewer_m2_2/handoff.md` and communicate with caller via `send_message`.

## Current Parent
- Conversation ID: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Updated: 2026-10-14T08:48:00Z

## Review Scope
- **Files to review**:
  - `moc-backend/reservations/services.py`
  - `moc-backend/reservations/views.py`
  - `moc-backend/reservations/serializers.py`
  - `moc-backend/reservations/models.py`
  - `moc-backend/foods/services.py`
  - `moc-backend/orders/services.py`
  - `moc-backend/payments/services.py`
  - `moc-backend/payments/views.py`
  - `moc-backend/payments/models.py`
  - `tests/e2e/test_milestone2_verification.py`
  - `tests/e2e/runner.py`
- **Interface contracts**:
  - `ORIGINAL_REQUEST.md`
  - `teamwork_preview_orchestrator_gen2/PROJECT.md`
  - `teamwork_preview_worker_m2_1/handoff.md`
- **Review criteria**:
  - Correctness of Phase 1 Redis hold (key format, 600s TTL, 409 Conflict with code BAN_DANG_BAN)
  - Correctness of Phase 2 pessimistic DB lock (`BanAn.objects.select_for_update().get(id=ban.id)` as table mutex, token validation, Redis key deletion)
  - BOM Material Inventory Deduction (deadlock prevention via sorted material IDs, stock validation, atomic deduction, audit logging in LichSuXuatNhapKho)
  - Refund Policy (tier calculation >24h 100%, 6-24h 50%, <6h 0%, no-show 0%, code format RF-{ma_dat_ban}-{YYYYMMDD}, PhieuHoanTien persistence)
  - Adversarial robustness & integrity violations

## Key Decisions Made
- Concluded code inspection and adversarial stress-testing.
- Determined verdict: **REQUEST_CHANGES** due to Critical transaction scoping and pessimistic locking integrity violations in `reservations/services.py`, `foods/services.py`, and `payments/services.py`.

## Artifact Index
- `.agents/teamwork/teamwork_preview_reviewer_m2_2/BRIEFING.md` — Agent briefing & working memory
- `.agents/teamwork/teamwork_preview_reviewer_m2_2/progress.md` — Liveness heartbeat and progress log
- `.agents/teamwork/teamwork_preview_reviewer_m2_2/handoff.md` — Final review report and verdict

## Review Checklist
- **Items reviewed**:
  - `moc-backend/reservations/services.py`: Phase 1 Redis hold (PASS), Phase 2 select_for_update (FAIL - not in transaction).
  - `moc-backend/foods/services.py`: BOM sorted-ID logic (PASS), select_for_update (FAIL - not in transaction).
  - `moc-backend/payments/services.py`: HMAC-SHA512 (PASS), Refund tiers (PASS), IPN select_for_update (FAIL - premature release).
  - `tests/e2e/test_milestone2_verification.py`: Test suite (FAIL - mocked transaction.atomic, omitted tao_dat_ban).
- **Verdict**: REQUEST_CHANGES
- **Unverified claims**: Worker claimed `select_for_update` acts as a table mutex in Phase 2; verified FALSE because it executes outside `transaction.atomic()` and raises `TransactionManagementError` in production.

## Attack Surface
- **Hypotheses tested**:
  - Hypothesis 1: `select_for_update()` outside transaction raises in PostgreSQL. Result: CONFIRMED. Django `SQLCompiler.as_sql()` raises `TransactionManagementError`.
  - Hypothesis 2: Concurrent IPNs can race because row lock released at line 155. Result: CONFIRMED.
  - Hypothesis 3: Reservation status change silently swallows BOM deduction errors. Result: CONFIRMED (`except Exception: pass`).
- **Vulnerabilities found**:
  - Critical: `DichVuDatBan.tao_dat_ban` select_for_update outside transaction.
  - Critical: `DichVuKho.khau_tru_nguyen_lieu_bom` and `hoan_tra_nguyen_lieu_bom` select_for_update outside transaction.
  - Major: Premature release of lock in `VNPayService.process_ipn`.
  - Major: Silent error swallowing in `DichVuDatBan.doi_trang_thai`.
- **Untested angles**: Live PostgreSQL connection pool behavior under saturation.
