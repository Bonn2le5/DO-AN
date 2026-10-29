# Dispatch: E2E Test Suite Architect & Writer

## Mission
You are the E2E Test Suite Architect & Writer for the Web App Nhà hàng Mộc project (E2E Testing Track).
Your responsibility is to design the opaque-box, requirement-driven test framework and initial automated test suite covering all requirements R1 to R5 and Acceptance Criteria in `ORIGINAL_REQUEST.md`:
1. Initialize `/Users/VuVan/Documents/DO-AN/TEST_INFRA.md` following the template in Project Pattern:
   - Test Philosophy (opaque-box, requirement-driven, independent of implementation internals).
   - Feature Inventory with Tier 1, Tier 2, Tier 3 mapping.
   - Real-World Application Scenarios (Tier 4).
   - Test runner command and directory layout (e.g. `tests/e2e/`).
2. Design and create automated test runner and test cases:
   - **Tier 1 (Feature Coverage >= 5 tests per feature group)**:
     - T1_backend: Test Django check, endpoints availability, seed data verification (100+ foods, tables, branches).
     - T1_vnpay: Test VNPay sandbox URL generation, checksum HMAC-SHA512 verification, IPN callback simulation.
     - T1_concurrency: Test Redis temporary reservation hold (`SET NX`), 10-minute expiry, and HTTP 409 Conflict rejection.
     - T1_realtime: Test WebSocket connection, message echo, FSM status transitions.
     - T1_recommendation_gis: Test `/api/recommendations/` returns items + explainable tags, `/api/branches/nearest/` returns nearest branch.
     - T1_frontend: Test TypeScript compilation (`npm run build`).
   - **Tier 2 (Boundary & Corner Cases >= 5 tests per feature group)**:
     - T2_vnpay: Invalid checksum, duplicate IPN idempotency, tampered amount.
     - T2_refund: Cancellation at >24h (100%), exactly 6h-24h (50%), <6h (0%), no-show (0%).
     - T2_concurrency: Simultaneous 2-user race condition on same table & time slot.
     - T2_fsm: Invalid state transition (e.g. `san_sang` -> `cho_tiep_nhan`).
   - **Tier 3 (Cross-Feature Combinations)**:
     - T3: Hold table -> Pay VNPay deposit -> IPN confirm -> Order dishes -> Inventory deduction.
   - **Tier 4 (Real-World Application Scenarios >= 5 scenarios)**:
     - End-to-end customer journey from nearest branch lookup to recommendation to table reservation, deposit payment, and real-time chat.
3. Write automated test scripts (e.g. Python pytest / requests / websockets in `tests/e2e/`).

## Mandatory Files to Read
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_1/PROJECT.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_survey_1/handoff.md`

## Deliverables
- Create `/Users/VuVan/Documents/DO-AN/TEST_INFRA.md`
- Create test files in `/Users/VuVan/Documents/DO-AN/tests/e2e/`
- Deliver report to `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_test_writer_e2e_1/handoff.md`
- When complete, publish `/Users/VuVan/Documents/DO-AN/TEST_READY.md`.

## 2026-10-14T03:17:58Z
You are E2E Test Suite Architect & Writer for Web App Nhà hàng Mộc (E2E Testing Track).
Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_test_writer_e2e_1
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_test_writer_e2e_1/DISPATCH.md.
Design TEST_INFRA.md and build the comprehensive automated test suite in tests/e2e/ covering Tiers 1-4 per project specifications.
Write your report to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_test_writer_e2e_1/handoff.md and publish TEST_READY.md when ready. Notify me via send_message when done.
