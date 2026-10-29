# BRIEFING — 2026-10-14T09:53:00Z

## Mission
Investigate ViewSet permissions on VNPay endpoints & table hold, QueryDict scalar extraction in process_ipn, and payment failure table release to formulate exact code-level fix recommendations for Milestone 2 Iteration 2.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigator, synthesizer
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_2
- Original parent: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Milestone: Milestone 2 Iteration 2

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Write only to working directory /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_2/
- Formulate exact code-level fix recommendations for get_permissions() in ViewSets, scalar dictionary extraction for QueryDict, and correct state transition to DA_HUY on payment failure

## Current Parent
- Conversation ID: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `ORIGINAL_REQUEST.md` & `PROJECT.md`
  - Iteration 1 Reports: `reviewer_m2_1`, `reviewer_m2_2`, `challenger_m2_1`, `challenger_m2_2`, `auditor_m2_1`
  - `moc-backend/payments/views.py`: `ThanhToanViewSet` missing `get_permissions()`, `vnpay_return` parameter dict extraction
  - `moc-backend/reservations/views.py`: `BanAnViewSet` missing `get_permissions()`, `DatBanViewSet.huy_dat_ban` unauthenticated `is_no_show`
  - `moc-backend/payments/services.py`: `VNPayService.process_ipn` QueryDict list wrapping, premature `transaction.atomic()` release, cancellation failure handling leaving `trang_thai = CHO_THANH_TOAN`
  - `moc-backend/reservations/services.py`: `tao_dat_ban` and `doi_trang_thai` transaction scoping
  - `moc-backend/foods/services.py`: `khau_tru_nguyen_lieu_bom` and `hoan_tra_nguyen_lieu_bom` transaction scoping
- **Key findings**:
  1. `ThanhToanViewSet` lacks `get_permissions()`, causing HTTP 401 Unauthorized on VNPay IPN and return callbacks.
  2. `BanAnViewSet` lacks `get_permissions()`, causing HTTP 401/403 on public table hold (`POST /api/tables/{id}/giu_ban/`).
  3. `dict(QueryDict)` in `process_ipn` wraps values into lists, corrupting HMAC calculation and rejecting 100% of authentic IPNs with code 97.
  4. Response code 24 sets `trang_thai_coc = THAT_BAI` without updating `dat_ban.trang_thai` to `DA_HUY`, permanently locking the table with HTTP 409 Conflict.
  5. Premature `transaction.atomic()` exits across multiple services release `select_for_update()` row locks before mutations occur.
- **Unexplored areas**: None within the scope of Milestone 2 Iteration 2.

## Key Decisions Made
- Formulated exact Before/After code blocks for all affected files.
- Provided full drop-in replacement artifacts (`proposed_payments_views.py`, `proposed_reservations_views.py`, `proposed_payments_services.py`).
- Implemented and executed empirical verification suite `proposed_test_enhancements.py` confirming 4/4 targeted defects fail on unpatched code.

## Artifact Index
- DISPATCH.md — Task instructions and received messages
- BRIEFING.md — Situational awareness and state
- progress.md — Liveness heartbeat
- handoff.md — 5-component handoff report
- proposed_payments_views.py — Complete replacement for `payments/views.py`
- proposed_reservations_views.py — Complete replacement for `reservations/views.py`
- proposed_payments_services.py — Complete replacement for `payments/services.py`
- proposed_test_enhancements.py — Regression test suite for all 4 failure modes
- m2_r2_fix_recommendations.patch — Unified diff patch
