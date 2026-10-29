# Dispatch: m2_r2_explorer_2

## Task
You are Explorer 2 for Milestone 2 Iteration 2: Webhook Permissions, QueryDict Handling & State Propagation.

## Context (Previous Gate Failures)
Reviewers and Challengers reported high-severity bugs:
- `payments/views.py:ThanhToanViewSet`: Default `permission_classes = [IsAuthenticated]` blocks external VNPay IPN and return callbacks with HTTP 401 Unauthorized.
- `reservations/views.py:BanAnViewSet`: `permission_classes = [LaNhanVienHoacChiDoc]` blocks customer table hold (`/api/tables/{id}/giu_ban/`) with HTTP 401/403.
- `payments/services.py:process_ipn`: Converting `request.query_params` with `dict(query_params)` wraps values in lists (`['v']`), corrupting HMAC-SHA512 calculation and rejecting authentic IPNs with code 97.
- Payment cancellation (code 24): Sets `trang_thai_coc = THAT_BAI` but leaves `dat_ban.trang_thai = CHO_THANH_TOAN`, causing table to remain permanently booked (`TABLE_ALREADY_BOOKED` / HTTP 409).

## Input Files
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen2/PROJECT.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m2_1/handoff.md`
- `moc-backend/payments/views.py`
- `moc-backend/reservations/views.py`
- `moc-backend/payments/services.py`

## Deliverables
Formulate exact code-level fix recommendations for `get_permissions()` in ViewSets, scalar dictionary extraction for QueryDict, and correct state transition to `DA_HUY` on payment failure. Write `handoff.md` in `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_2/handoff.md`.

## 2026-10-14T08:56:13Z
You are m2_r2_explorer_2, Explorer 2 for Milestone 2 Iteration 2.
Your working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_2
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_2/DISPATCH.md
MANDATORY: Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and the review reports from Iteration 1.
Formulate fix recommendations for ViewSet permissions on VNPay endpoints & table hold, QueryDict scalar extraction in process_ipn, and payment failure table release.
Deliver report to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_2/handoff.md and notify the caller.
