# BRIEFING — 2026-10-14T08:34:00Z

## Mission
Implement Milestone 2: VNPay Sandbox Deposit Payment & 2-Phase Table Concurrency Control, Deposit Refund & Cancellation Policy, and BOM Material Inventory Deduction.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m2_1
- Original parent: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Milestone: Milestone 2: VNPay Sandbox Deposit Payment & Table Concurrency Control

## 🔒 Key Constraints
- DO NOT CHEAT: Genuine implementation, no hardcoded test results, no dummy facade implementations, maintain real state.
- Write only inside owned project backend files and `.agents/teamwork/teamwork_preview_worker_m2_1/`.
- Django check must report 0 issues.
- All tier 1, tier 2, and adversarial tests must continue to pass.
- Implement comprehensive milestone 2 verification tests.

## Current Parent
- Conversation ID: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Updated: 2026-10-14T08:30:18Z

## Task Summary
- **What to build**: Full implementation of Milestone 2 (VNPay 2.1.0, 2-phase concurrency control, deposit refund, BOM inventory deduction).
- **Success criteria**: 0 Django issues, all Tiers 1-4 pass (60 tests), M1 adversarial tests pass (34 tests), M2 verification tests pass (26 tests).
- **Interface contracts**: `PROJECT.md` contracts 1, 2, 3.
- **Code layout**: Django modular backend in `moc-backend/`.

## Key Decisions Made
- Fail-fast IPN evaluation: Validate HMAC checksum before starting any DB transaction to protect DB connection pools from spoofed IPN requests.
- Strict Resource Ordering in BOM deduction: Sort ingredient IDs ascending before acquiring PostgreSQL row-level locks via `select_for_update()`, eliminating deadlocks.
- Fallback caching mechanism `_safe_cache()`: Primary `RedisCache` with automatic fallback to `LocMemCache` for offline/isolated sandbox test environments.
- Backward compatibility: Provide full model, serializer, and viewset aliases (e.g. `RefundReceipt`, `InventoryService`, `TableViewSet`, `ReservationViewSet`).

## Artifact Index
- `.agents/teamwork/teamwork_preview_worker_m2_1/DISPATCH.md` — assignment & communications
- `.agents/teamwork/teamwork_preview_worker_m2_1/BRIEFING.md` — persistent memory index
- `.agents/teamwork/teamwork_preview_worker_m2_1/progress.md` — heartbeat and progress
- `.agents/teamwork/teamwork_preview_worker_m2_1/handoff.md` — final handoff report

## Change Tracker
- **Files modified**:
  * `moc-backend/config/settings.py`: Redis CACHES and VNPay Sandbox configuration.
  * `moc-backend/payments/models.py`: Added `PhieuHoanTien` model, aliases, and properties.
  * `moc-backend/payments/admin.py`: Registered `PhieuHoanTien` in Django Admin.
  * `moc-backend/payments/migrations/0002_phieuhoantien.py`: Migration for `PhieuHoanTien`.
  * `moc-backend/payments/services.py`: `VNPayService` (URL builder, HMAC, IPN 00/01/02/04/97) & `RefundService`.
  * `moc-backend/payments/serializers.py`: `PhieuHoanTienSerializer`, `VNPayCreatePaymentSerializer`.
  * `moc-backend/payments/views.py`: `vnpay_create`, `vnpay_tao_phien`, `vnpay_return`, `vnpay_ipn`, `PhieuHoanTienViewSet`.
  * `moc-backend/payments/urls.py`: Dedicated routes for payments and VNPay endpoints.
  * `moc-backend/api/urls.py`: Registered refund receipt routes and explicit dual VNPay & table hold paths.
  * `moc-backend/reservations/services.py`: 2-Phase Concurrency Control (`giu_ban_tam_thoi`, pessimistic row lock in `tao_dat_ban`, `doi_trang_thai`).
  * `moc-backend/reservations/serializers.py`: Compatibility fields `ban_an_id`, `ten_ban`, `so_ban`, aliases.
  * `moc-backend/reservations/views.py`: `giu_ban`, `giu_ban_hyphen`, `giu_ban_frontend`, `huy_dat_ban`, `cancel`.
  * `moc-backend/foods/services.py`: `DichVuKho.khau_tru_nguyen_lieu_bom` with sorted-ID deadlock prevention and `LichSuXuatNhapKho` audit logging.
  * `moc-backend/orders/services.py`: Hooked BOM deduction and reversal into `doi_trang_thai`.
  * `tests/e2e/test_milestone2_verification.py`: 26 comprehensive unit/integration tests for Milestone 2.
- **Build status**: PASS (`python manage.py check`: 0 issues).
- **Pending issues**: None.

## Quality Status
- **Build/test result**:
  * `manage.py check`: 0 issues (exit code 0).
  * `tests/e2e/runner.py`: 60/60 tests PASSED (100%).
  * `tests/e2e/test_adversarial_challenger_m1.py`: 18/18 tests PASSED (100%).
  * `tests/e2e/test_adversarial_stress_m1.py`: 16/16 tests PASSED (100%).
  * `tests/e2e/test_milestone2_verification.py`: 26/26 tests PASSED (100%).
- **Lint status**: 0 syntax/lint errors.
- **Tests added/modified**: 26 new tests covering all 6 Milestone 2 feature areas.

## Loaded Skills
- None
