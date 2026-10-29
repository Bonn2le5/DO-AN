# Dispatch Assignment: Milestone 6 Lead E2E Worker (m6_worker_e2e)

## Context
You are Worker `m6_worker_e2e` assigned to execute and certify the full End-to-End integration verification and adversarial hardening for the Web App Nhà hàng Mộc project (Milestone 6).

Your Working Directory: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m6_1`

## Authoritative Documents to Read First
1. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` (MANDATORY — Read all requirements R1–R5 and Acceptance Criteria)
2. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen5/PROJECT.md`
3. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen5/GATE_STATUS.md`

## MANDATORY INTEGRITY WARNING
> DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Execution and Verification Tasks
Execute the following verification commands in order and document exact stdout, exit codes, and test counts:

1. **Frontend Production Compilation**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN/moc-frontend && npx tsc --noEmit && npm run build
   ```
   Confirm exit code 0 and zero TypeScript compilation errors.

2. **Django Backend System Health Check**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN && moc-backend/.venv/bin/python moc-backend/manage.py check
   ```
   Confirm 0 issues identified.

3. **Master E2E Automated Test Suite (Tiers 1–4)**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN && moc-backend/.venv/bin/python tests/e2e/runner.py
   ```
   Confirm 60/60 tests pass (100.0% pass rate).

4. **Comprehensive App Integration Tests**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN && moc-backend/.venv/bin/python moc-backend/manage.py test accounts foods branches reservations orders payments carts promotions reviews chat recommendations analytics
   ```
   Document all passing tests.

5. **Adversarial Hardening Suites**:
   - `moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m1.py`
   - `moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m2.py`
   - `moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m3.py`
   - `moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4.py`
   - `TESTING=1 moc-backend/.venv/bin/python tests/e2e/test_adversarial_m5_portals.py`
   - `moc-backend/.venv/bin/python tests/e2e/test_adversarial_m5_realtime.py`

6. **Systematic Acceptance Criteria Checklist**:
   Verify and document every criterion in `ORIGINAL_REQUEST.md`:
   - System Integrity & Stability (`python manage.py check`, `npm run build`, PostgreSQL test data).
   - Table Reservation & VNPay (Redis 10m TTL lock, HTTP 409, VNPay Sandbox URL HMAC-SHA512, IPN webhook, refund calculations).
   - Realtime & AI (WebSocket chat DB persistence, live Order FSM stepper push, AI recommendation Top-N + explainable tags + cold start, PostGIS GIS nearest branch).
   - Frontend Portals (Customer flow, Staff Live Chat, Admin Reservations, Menu/Inventory, Reviews, Orders).

## Deliverables
Write your 5-component handoff report (Observation, Logic Chain, Caveats, Conclusion, Verification Method) to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m6_1/handoff.md`
And notify the orchestrator via send_message.


## 2026-10-15T00:36:28Z
You are Worker m6_worker_e2e assigned to execute the full End-to-End integration verification and adversarial hardening for the Web App Nhà hàng Mộc project (Milestone 6).

Your Working Directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m6_1
All your working metadata, progress.md, and handoff.md MUST be saved in your working directory.

MANDATORY FIRST STEP: Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md completely.
Also read:
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen5/PROJECT.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m6_1/DISPATCH.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen5/GATE_STATUS.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Execution Tasks:
1. Run frontend build and typecheck:
   - `cd /Users/VuVan/Documents/DO-AN/moc-frontend && npx tsc --noEmit && npm run build` (Confirm 0 errors)
2. Run backend system check:
   - `cd /Users/VuVan/Documents/DO-AN && moc-backend/.venv/bin/python moc-backend/manage.py check` (Confirm 0 issues)
3. Run master E2E automated suite:
   - `cd /Users/VuVan/Documents/DO-AN && moc-backend/.venv/bin/python tests/e2e/runner.py` (Confirm 60/60 pass)
4. Run Django app integration test suite:
   - `cd /Users/VuVan/Documents/DO-AN && moc-backend/.venv/bin/python moc-backend/manage.py test accounts foods branches reservations orders payments carts promotions reviews chat recommendations analytics`
5. Run cross-module adversarial hardening suites:
   - `moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m1.py`
   - `moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m2.py`
   - `moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m3.py`
   - `moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4.py`
   - `TESTING=1 moc-backend/.venv/bin/python tests/e2e/test_adversarial_m5_portals.py`
   - `moc-backend/.venv/bin/python tests/e2e/test_adversarial_m5_realtime.py`
6. Document full systematic evaluation of all Acceptance Criteria in ORIGINAL_REQUEST.md.

Write your 5-component handoff report (Observation, Logic Chain, Caveats, Conclusion, Verification Method) to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m6_1/handoff.md`
And notify the orchestrator via send_message.
