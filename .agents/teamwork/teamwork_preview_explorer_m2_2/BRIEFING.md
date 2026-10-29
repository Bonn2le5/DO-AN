# BRIEFING — 2026-10-14T08:11:00Z

## Mission
Investigate and design VNPay Sandbox payment creation, return URL callback, IPN verification, settings configuration, reservation/order integration, and automated refund execution for Milestone 2.

## 🔒 My Identity
- Archetype: explorer
- Roles: Technical Explorer 2 (Milestone 2)
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_2
- Original parent: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Milestone: Milestone 2 (VNPay Integration & Payment Verification)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement code directly in backend until instructed / Explorer produces design and handoff.
- Investigate backend codebase thoroughly and design precise, production-ready specifications.

## Current Parent
- Conversation ID: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `ORIGINAL_REQUEST.md`, `PROJECT.md`, `TEST_INFRA.md`, `TEST_READY.md`
  - `moc_schema_tieng_viet.sql` (lines 19-27, 268-326, 436-460)
  - `moc-backend/payments/` (`models.py`, `views.py`, `serializers.py`, `migrations/0001_initial.py`)
  - `moc-backend/reservations/` (`models.py`, `views.py`, `serializers.py`, `services.py`)
  - `moc-backend/orders/` (`models.py`, `views.py`, `serializers.py`, `services.py`)
  - `moc-backend/api/urls.py` and `moc-backend/config/settings.py`
  - `tests/e2e/helpers/vnpay_oracle.py`, `tests/e2e/helpers/refund_calculator.py`
  - `tests/e2e/tier1/test_t1_vnpay.py`, `tests/e2e/tier2/test_t2_vnpay.py`, `tests/e2e/tier2/test_t2_refund.py`, `tests/e2e/tier3/test_t3_combinations.py`
  - `moc-frontend/src/api/reservations.api.ts`, `moc-frontend/src/pages/reservation/PaymentStep.tsx`
- **Key findings**:
  1. VNPay v2.1.0 parameters and HMAC-SHA512 checksum verified with authoritative oracle `vnpay_oracle.py`. Amount must be multiplied by 100, keys sorted in ASCII order, values encoded with `quote_plus`.
  2. IPN webhook response codes strictly defined: '00' (Success), '01' (Order not found), '02' (Already confirmed/idempotent), '04' (Invalid amount), '97' (Invalid Checksum).
  3. `thanh_toan` model in DB uses enum `trang_thai_thanh_toan`: `'cho_xu_ly'`, `'thanh_cong'`, `'that_bai'`, `'da_hoan_tien'`. Note: use `'thanh_cong'` in DB rather than `'da_thanh_toan'` to satisfy schema enum constraint.
  4. Cancellation refund policy rules: >24h = 100%, 6-24h = 50%, <6h = 0%, no-show = 0%. `PhieuHoanTien` receipt structure generated with code `RF-{ma_dat_ban}-{YYYYMMDD}`.
  5. Dual API routes required: English (`/api/payments/vnpay/...`) and Vietnamese (`/api/thanh-toan/vnpay/...`, `/api/thanh-toan/vnpay/tao-phien/`).
- **Unexplored areas**: None. All required files, specifications, and edge cases mapped.

## Key Decisions Made
- Architecture planned with dedicated `payments/services.py` containing `VNPayService` and `RefundService`.
- Model aliases and property getters/setters designed to ensure 100% backward compatibility for English and Vietnamese callers.
- Writing comprehensive 5-component handoff report.

## Artifact Index
- DISPATCH.md — Task assignment and instructions
- BRIEFING.md — Persistent working memory
- progress.md — Liveness heartbeat
- handoff.md — Complete 5-component technical investigation and architecture report
