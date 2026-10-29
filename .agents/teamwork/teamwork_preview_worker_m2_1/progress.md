# Progress Log - m2_worker_1

- **Last visited**: 2026-10-14T08:31:00Z
- **Current status**: Running and validating comprehensive Milestone 2 verification test suite.
- **Completed steps**:
  1. Configured Redis CACHES & VNPay settings in `moc-backend/config/settings.py`.
  2. Created `PhieuHoanTien` model in `moc-backend/payments/models.py`, registered in `payments/admin.py`, created clean migration `0002_phieuhoantien.py`.
  3. Implemented VNPay 2.1.0 service (`VNPayService`) with HMAC-SHA512 URL builder, signature verification, and 5-stage IPN handler (codes 00, 01, 02, 04, 97) in `payments/services.py`.
  4. Implemented deposit refund calculation & receipt generation (`RefundService`) in `payments/services.py` with 4 time brackets (>24h 100%, 6-24h 50%, <6h 0%, no-show 0%).
  5. Implemented VNPay endpoints (`vnpay/create`, `vnpay/tao-phien`, `vnpay/return`, `vnpay/ipn`) and `PhieuHoanTienViewSet` in `payments/views.py`, with serializers in `payments/serializers.py` and dual routes in `payments/urls.py` & `api/urls.py`.
  6. Implemented 2-Phase Table Concurrency Control in `reservations/services.py`:
     - Phase 1 Redis hold `table_hold:{id}:{date}:{time}` with TTL 600s, HTTP 409 format (`code: "BAN_DANG_BAN"`).
     - Phase 2 pessimistic lock via `BanAn.objects.select_for_update()`, token verification, and Redis key cleanup.
     - Dual endpoints `/tables/{id}/giu_ban/`, `/ban-an/{id}/giu_ban/`, and `/dat-ban/giu-ban/`.
     - Integrated deposit refund calculation and `PhieuHoanTien` generation in `DatBanViewSet.huy_dat_ban`.
  7. Implemented BOM Material Inventory Deduction in `foods/services.py` (`DichVuKho.khau_tru_nguyen_lieu_bom`) with strictly ascending ID resource ordering for deadlock prevention, stockout validation, and `LichSuXuatNhapKho` audit logging; hooked into `orders/services.py:doi_trang_thai`.
  8. Verified `manage.py check` (0 issues).
  9. Verified all 60 tests across Tiers 1-4 pass 100%.
  10. Verified all 34 adversarial tests (challenger + stress) pass 100%.
- **Next steps**:
  - Run and verify new `tests/e2e/test_milestone2_verification.py`.
  - Update BRIEFING.md.
  - Write handoff report `handoff.md`.
