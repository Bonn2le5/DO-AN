# Dispatch: m2_worker_1

## Task
You are the Implementation Worker for Milestone 2: VNPay Sandbox Deposit Payment & Table Concurrency Control.

## Working Directory
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m2_1`

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Input Context (MANDATORY READ)
You MUST read the following authoritative reports before modifying code:
1. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
2. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen2/PROJECT.md`
3. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m2_1/handoff.md` (Detailed VNPay 2.1.0 and Refund Policy specifications & blueprints)
4. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_1/handoff.md` (2-Phase Concurrency Control & BOM Deduction architecture)
5. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_2/handoff.md` (VNPay payments architecture, dual route mappings, and serializers)

## Code Ownership & Deliverables
You have exclusive write ownership of the following backend files:
- `moc-backend/config/settings.py` (Add Redis CACHES configuration, add VNPAY configuration variables)
- `moc-backend/payments/models.py` (Add `PhieuHoanTien` / `RefundReceipt` model, register admin in `payments/admin.py`)
- `moc-backend/payments/services.py` (Create comprehensive VNPay 2.1.0 URL builder with HMAC-SHA512, signature verification, IPN evaluation 00/01/02/04/97, and refund calculator)
- `moc-backend/payments/serializers.py` (Add serializers for VNPay create, IPN, return, PhieuHoanTien)
- `moc-backend/payments/views.py` (Add VNPay endpoints: create payment, return callback, IPN webhook, frontend `tao-phien`)
- `moc-backend/payments/urls.py` & `moc-backend/api/urls.py` (Dual routes for `/api/payments/vnpay/...` and `/api/thanh-toan/vnpay/...`)
- `moc-backend/reservations/views.py` & `moc-backend/reservations/services.py` (Implement Phase 1 Redis hold `table_hold:{id}:{date}:{time}` with HTTP 409 Conflict format, dual routes `/api/tables/{id}/giu_ban/`, `/api/ban-an/{id}/giu_ban/`, and list action `/api/dat-ban/giu-ban/`; Phase 2 pessimistic lock via `BanAn.objects.select_for_update()`; automated refund calculation and `PhieuHoanTien` generation in `huy_dat_ban`)
- `moc-backend/reservations/serializers.py` (Expose `ban_an_id`, `ten_ban`, `so_ban`, ensure compatibility with frontend `reservations.api.ts`)
- `moc-backend/foods/services.py` & `moc-backend/orders/services.py` (Implement BOM Material Inventory Deduction `DichVuKho.khau_tru_nguyen_lieu_bom()` with sorted-ID deadlock prevention, stock check, deduction, and `LichSuXuatNhapKho` audit logging)

## Verification Steps (Required in handoff)
1. Generate migration for `PhieuHoanTien`:
   `./moc-backend/.venv/bin/python moc-backend/manage.py makemigrations payments`
   `./moc-backend/.venv/bin/python moc-backend/manage.py migrate`
2. Run Django system check (MUST be 0 issues):
   `./moc-backend/.venv/bin/python moc-backend/manage.py check`
3. Run existing test suites:
   `./moc-backend/.venv/bin/python tests/e2e/runner.py --tier 1`
   `./moc-backend/.venv/bin/python tests/e2e/runner.py --tier 2`
4. Run Milestone 1 Adversarial harness:
   `./moc-backend/.venv/bin/python moc-backend/proposed_test_adversarial_challenger_m1.py`
5. Write unit/integration tests verifying:
   - Phase 1 Redis hold: successful hold, expiration TTL 600s, HTTP 409 Conflict format on duplicate.
   - Phase 2 Pessimistic lock: booking confirmation, Redis key cleanup.
   - VNPay URL generation: exact HMAC-SHA512 checksum match with `vnpay_oracle.py`.
   - VNPay IPN webhook: status codes 00, 01, 02, 04, 97, idempotency.
   - Deposit refund calculation: >24h (100%), 6–24h (50%), <6h (0%), no-show (0%), and `PhieuHoanTien` record generation.
   - BOM material deduction: sorted-ID locking, stock deduction, `LichSuXuatNhapKho` entry.

Write your complete handoff report to `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m2_1/handoff.md` and notify the caller when done.


## 2026-10-14T08:13:04Z
[Message] timestamp=2026-10-14T08:13:04Z sender=3b4ac039-b543-49a4-9b3d-21e996771d3e priority=MESSAGE_PRIORITY_HIGH
content=You are m2_worker_1, the Implementation Worker for Milestone 2: VNPay Sandbox Deposit Payment & Table Concurrency Control.
Your working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m2_1

MANDATORY READ:
- Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m2_1/DISPATCH.md
- Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md
- Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen2/PROJECT.md
- Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m2_1/handoff.md
- Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_1/handoff.md
- Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_2/handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Implement:
1. Redis CACHES configuration and VNPay settings in moc-backend/config/settings.py.
2. PhieuHoanTien model in moc-backend/payments/models.py, registered in payments/admin.py, run makemigrations payments & migrate.
3. VNPay 2.1.0 services, serializers, views, and dual routes in payments (URL builder, IPN webhook 00/01/02/04/97, return callback, frontend tao-phien).
4. 2-Phase Table Concurrency Control in reservations:
   - Phase 1 Redis hold (SET NX EX 600, HTTP 409 Conflict format, dual routes /tables/{id}/giu_ban/ and list /dat-ban/giu-ban/).
   - Phase 2 pessimistic locking via BanAn.objects.select_for_update(), token verification, Redis key cleanup.
5. Deposit refund & cancellation policy in DatBanViewSet.huy_dat_ban (>24h 100%, 6-24h 50%, <6h 0%, no-show 0%) and PhieuHoanTien creation.
6. BOM Material Inventory Deduction in foods/services.py with sorted-ID deadlock prevention, stock check, deduction, and LichSuXuatNhapKho logging. Hook into order confirmation.
7. Verification: Run python manage.py check (0 issues), run Tier 1 & 2 tests, adversarial tests, and write/run milestone 2 verification tests.

Write your handoff report to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m2_1/handoff.md and notify the caller when done.


## 2026-10-14T08:30:18Z
[Message] timestamp=2026-10-14T08:30:18Z sender=3b4ac039-b543-49a4-9b3d-21e996771d3e priority=MESSAGE_PRIORITY_HIGH
content=**Context**: Milestone 2 Implementation Liveness Check
**Content**: Please provide a brief status update on your progress: which components (settings, payments, reservations concurrency, BOM inventory, migrations, tests) have been completed so far and what are you currently working on? Please remember to update your progress.md.
**Action**: Reply with your current status and update progress.md.
