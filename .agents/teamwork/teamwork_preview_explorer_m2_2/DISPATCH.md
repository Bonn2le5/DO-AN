# Dispatch: m2_explorer_2

## Task
You are Technical Explorer 2 for Milestone 2: VNPay Integration & API Route Mapping.

## Scope & Objective
Read:
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen2/PROJECT.md`
- `/Users/VuVan/Documents/DO-AN/moc-backend/payments/` (models, views, serializers, urls)
- `/Users/VuVan/Documents/DO-AN/moc-backend/api/urls.py`
- `/Users/VuVan/Documents/DO-AN/moc-backend/config/settings.py`

Investigate and provide technical design for:
1. VNPay Sandbox Payment Module:
   - Create payment URL endpoint: `POST /api/payments/vnpay/create/` and `/api/thanh-toan/vnpay/create/`.
   - Return URL callback endpoint: `GET /api/payments/vnpay/return/` and `/api/thanh-toan/vnpay/return/`.
   - IPN webhook endpoint: `GET /api/payments/vnpay/ipn/` and `/api/thanh-toan/vnpay/ipn/`.
   - Settings & Environment configuration (`VNPAY_TMN_CODE`, `VNPAY_HASH_SECRET`, `VNPAY_URL`, `VNPAY_RETURN_URL`).
2. Integration with Reservations & Orders:
   - Linking `ThanhToan` to `DatBan` (deposit) or `DonHang` (order).
   - Status updates upon IPN verification: updating `ThanhToan.trang_thai = 'da_thanh_toan'` and updating `DatBan.trang_thai = 'da_xac_nhan'` or `DonHang.trang_thai = 'da_xac_nhan'`.
   - Dual routing and serialization for both English (`payments/`) and Vietnamese (`thanh-toan/`) endpoints.
3. Automated Refund Execution:
   - Cancellation view: `POST /api/reservations/{id}/huy_dat_ban/`.
   - Calculation of hours until reservation: `gio_den - now()`.
   - Refund record creation (`PhieuHoanTien`), state transition to `da_huy`.

Deliver your findings and concrete implementation architecture in `handoff.md` in your directory (`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_2/handoff.md`).


## 2026-10-14T07:59:40Z
You are m2_explorer_2, Technical Explorer 2 for Milestone 2.
Your working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_2
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_2/DISPATCH.md
MANDATORY: Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen2/PROJECT.md before starting work.
Investigate and provide technical design for VNPay Sandbox payment creation, return URL callback, IPN webhook verification, settings configuration, and integration with DatBan/DonHang.
Write your complete findings and architecture to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_2/handoff.md and notify the caller when done.
