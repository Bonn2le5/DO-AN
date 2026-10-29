# BRIEFING — 2026-10-14T15:46:00Z

## Mission
Adversarially and empirically stress-test Milestone 3: 6-State Order Finite State Machine (FSM), Concurrent Transitions, Actor/Authorization Enforcement, and BOM Raw Material Inventory Deduction/Refund Hooks.

## 🔒 My Identity
- Archetype: EMPIRICAL CHALLENGER
- Roles: critic, specialist
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m3_2
- Original parent: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
- Milestone: M3 (Real-Time Communication & Order FSM)
- Instance: m3_challenger_2

## 🔒 Key Constraints
- Review-only — do NOT modify implementation code. Report failures as findings.
- Empirical verification mandatory — write and execute adversarial tests, generators, oracles, and stress harnesses.
- Must reproduce any bug empirically.
- Metadata only in `.agents/teamwork/teamwork_preview_challenger_m3_2/`. Verification scripts must run from permitted project locations (e.g. backend / scratch, never .agents/teamwork/).

## Current Parent
- Conversation ID: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
- Updated: 2026-10-14T15:46:00Z

## Review Scope
- **Files reviewed**:
  - `moc-backend/orders/services.py`
  - `moc-backend/orders/views.py`
  - `moc-backend/orders/models.py`
  - `moc-backend/orders/consumers.py`
  - `moc-backend/orders/routing.py`
  - `moc-backend/foods/services.py`
  - `moc-backend/chat/consumers.py`
  - `moc-backend/chat/views.py`
  - `moc-backend/config/asgi.py`
  - `moc-backend/config/middleware.py`
  - `moc-backend/api/ws_auth.py`
  - `moc-backend/orders/tests.py`
  - `moc-backend/chat/tests.py`
  - `tests/e2e/tier2/test_t2_fsm.py`
  - `tests/e2e/tier1/test_t1_realtime.py`
  - `moc-backend/orders/tests_challenger_m3.py` (Challenger Empirical Suite)
- **Interface contracts**: PROJECT.md, moc_schema_tieng_viet.sql, ORIGINAL_REQUEST.md
- **Review criteria**:
  1. 6-state FSM matrix & strict transition rules (reject skips, reversals, self-transitions, unknown states, terminal immutability).
  2. Actor permissions (customer can only cancel pending `cho_tiep_nhan`; staff can execute legal transitions).
  3. Concurrency race stress testing with `select_for_update` row locking.
  4. BOM raw material inventory deduction on `da_xac_nhan` and refund on `da_huy`.
  5. WebSocket security, persistence before broadcast, authentication & authorization.

## Key Decisions Made
- Executed full 6x6 transition matrix test suite (36 state pairs: 8 legal, 28 illegal).
- Verified customer cancellation permissions restricted strictly to pending `cho_tiep_nhan` orders.
- Verified BOM inventory deduction on `da_xac_nhan`, refunds on `da_huy` from `da_xac_nhan` and `dang_che_bien`, and zero refund on `cho_tiep_nhan`.
- Verified insufficient inventory blocks order confirmation atomically and restores initial state with 0 corruption.
- Verified multi-threaded concurrency race control with pessimistic row locking and idempotent BOM execution.
- Verified REST API endpoint security, scoping, and alias routing (`trang_thai`, `chuyen_trang_thai`, `status`).
- Verified WebSocket token authentication (4401), authorization scoping (4403), and payload limits (5000 chars).
- Verdict: **APPROVE**.

## Attack Surface
- **Hypotheses tested**:
  - H1: An illegal transition (skip or reverse) could mutate the order status. -> REJECTED (all 28 illegal transitions raised `ValidationError`, states remained intact).
  - H2: Terminal states (`hoan_tat`, `da_huy`) could be re-opened. -> REJECTED (terminal states 100% immutable).
  - H3: Customer could cancel an order after kitchen started cooking (`dang_che_bien` or `san_sang`). -> REJECTED (`PermissionDenied` raised).
  - H4: Customer B could inspect or cancel Customer A's order via REST API or WebSocket. -> REJECTED (REST returns 404, WebSocket returns 4403).
  - H5: Confirming order without sufficient raw materials leaves order in inconsistent state or deducts negative inventory. -> REJECTED (`ValidationError` raised, atomic transaction rolls back, inventory uncorrupted).
  - H6: Concurrent confirmations lead to duplicate BOM deductions. -> REJECTED (idempotent BOM check + row locking prevents duplicate deduction).
- **Vulnerabilities found**: None. System is resilient and robustly defended against adversarial attack vectors.
- **Untested angles**: Live production PostgreSQL row locks vs SQLite table lock degradation (noted in caveats, tested with simulated concurrency).

## Loaded Skills
- None specified.

## Artifact Index
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m3_2/BRIEFING.md` — Agent briefing & working memory
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m3_2/progress.md` — Liveness heartbeat & task progress
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m3_2/handoff.md` — Final handoff report & verdict
- `/Users/VuVan/Documents/DO-AN/moc-backend/orders/tests_challenger_m3.py` — Adversarial empirical test suite (20 tests)
