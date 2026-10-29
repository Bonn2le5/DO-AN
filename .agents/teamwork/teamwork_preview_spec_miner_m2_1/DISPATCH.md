# Dispatch: m2_spec_miner_1

## Task
You are the Specification Miner for Milestone 2 (VNPay Sandbox & Deposit Refund Policy).

## Scope & Objective
Read:
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen2/PROJECT.md`
- `/Users/VuVan/Documents/DO-AN/moc-backend/payments/models.py`
- `/Users/VuVan/Documents/DO-AN/moc-backend/reservations/models.py`
- `/Users/VuVan/Documents/DO-AN/moc_schema_tieng_viet.sql`

Investigate and document precise specifications for:
1. VNPay Sandbox 2.1.0 specifications:
   - Required parameters (`vnp_Version`, `vnp_Command`, `vnp_TmnCode`, `vnp_Amount`, `vnp_CreateDate`, `vnp_CurrCode`, `vnp_IpAddr`, `vnp_Locale`, `vnp_OrderInfo`, `vnp_OrderType`, `vnp_ReturnUrl`, `vnp_TxnRef`, `vnp_SecureHash`).
   - Query parameter sorting (ASCII alphabetical order, URL encoding rules).
   - HMAC-SHA512 checksum calculation logic and verification.
   - Return URL callback parameters and verification.
   - Server-to-server IPN webhook parameters, signature verification, response format JSON `{"RspCode": "00", "Message": "Confirm Success"}` with status codes `00` (success), `01` (order not found), `02` (order already confirmed/duplicate), `04` (invalid amount), `97` (invalid checksum).
2. Deposit Refund & Cancellation Policy:
   - Rules: >24h before booking: 100% refund; 6–24h before booking: 50% refund; <6h before booking: 0% refund.
   - `PhieuHoanTien` record structure and generation: calculation of `so_tien_hoan`, `phan_tram_hoan`, reference to `ThanhToan` and `DatBan`.
   - Cancellation endpoint specifications (`POST /api/reservations/{id}/huy_dat_ban/` and `/api/dat-ban/{id}/huy_dat_ban/`).

Deliver a comprehensive specification report in `handoff.md` in your directory (`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m2_1/handoff.md`).


## 2026-10-14T07:59:40Z
You are m2_spec_miner_1, the Specification Miner for Milestone 2.
Your working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m2_1
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m2_1/DISPATCH.md
MANDATORY: Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen2/PROJECT.md before starting work.
Investigate and document precise specifications for VNPay Sandbox 2.1.0 (params, HMAC-SHA512 checksum, IPN response codes and idempotency) and Deposit Cancellation / Refund Policies.
Write your complete specification findings to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m2_1/handoff.md and notify the caller when done.
