# BRIEFING — 2026-10-15T07:07:00Z

## Mission
Empirically stress-test Milestone 5 (Frontend Synchronization & Staff/Admin Portals) for Web App Nhà hàng Mộc, focusing on review moderation permissions, inventory/BOM concurrency, order FSM admin transitions & audit logging, and table reservation floor plan data consistency.

## 🔒 My Identity
- Archetype: EMPIRICAL CHALLENGER
- Roles: critic, specialist
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m5_2
- Original parent: 4569185e-dbd8-4811-a385-d58c3b35b3ca
- Milestone: Milestone 5
- Instance: 2 of 2

## 🔒 Key Constraints
- Review-only — do NOT modify implementation code (report failures as findings)
- Metadata strictly in .agents/teamwork/teamwork_preview_challenger_m5_2
- Test harnesses in designated test directories (tests/e2e/test_adversarial_m5_portals.py)
- Binary verdict: APPROVE or REQUEST_CHANGES
- Send report back via send_message to parent

## Current Parent
- Conversation ID: 4569185e-dbd8-4811-a385-d58c3b35b3ca
- Updated: 2026-10-15T07:07:00Z

## Review Scope
- **Files to review**: reviews/views.py, foods/views.py, orders/views.py, reservations/views.py, moc-frontend/src/api/admin.api.ts, moc-frontend/src/pages/admin/*
- **Interface contracts**: PROJECT.md, ORIGINAL_REQUEST.md, worker_m5_1/handoff.md
- **Review criteria**: Permission enforcement, state machine transitions, concurrent inventory adjustments, audit logging, floor plan data consistency

## Attack Surface
- **Hypotheses tested**:
  1. Review moderation visibility isolation & tenant protection
  2. Review deletion authorization & rating recalculation
  3. Manual stock-in/stock-out transaction endpoint (LichSuKhoViewSet)
  4. Automated BOM deduction and cancellation reversal
  5. Order FSM complete lifecycle & audit logging integrity
  6. Table floor plan slot filtering & 10-thread hold lock concurrency race
- **Vulnerabilities found**:
  1. `LichSuKhoViewSet` fails with `IntegrityError` (NOT NULL on `ton_kho_truoc`) when staff creates stock transactions via `POST /api/inventory-transactions/`, and never adjusts `NguyenLieu.ton_kho_hien_tai`.
  2. `DanhGiaViewSet` lacks `perform_destroy` authorization check, allowing any authenticated customer to permanently delete any other customer's review with HTTP 204, without updating dish ratings.
- **Untested angles**:
  - Live browser DOM rendering (tested at API contract & DRF layer).

## Loaded Skills
None specified in dispatch.

## Key Decisions Made
- Designed and executed 16-scenario adversarial stress suite `tests/e2e/test_adversarial_m5_portals.py`.
- Evaluated Django backend checks: `manage.py check` (0 issues), unit tests (32/32 OK).
- Evaluated empirical adversarial suite: 14/16 passed (87.5%), 2 failed.
- Verdict formulated: REQUEST_CHANGES due to manual inventory crash and review deletion authorization vulnerability.

## Artifact Index
- DISPATCH.md — Initial task dispatch
- progress.md — Liveness heartbeat and milestone tracking
- tests/e2e/test_adversarial_m5_portals.py — 16-test empirical adversarial harness
- handoff.md — 5-Component handoff report with REQUEST_CHANGES verdict
