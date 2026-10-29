# Dispatch Instructions for Challenger m4_challenger_1

## Mission
Adversarially and empirically stress-test Milestone 4 AI Recommendation Engine:
1. Verify TF-IDF and Cosine similarity mathematical correctness without external libraries.
2. Verify interaction weights (`xem=1, yeu_thich=2, them_gio_hang=3, dat_mon=4, danh_gia=5`) and user profile calculations.
3. Stress-test Cold-Start popularity fallback: verify scores are strictly bounded in [0.0, 1.0] without Decimal overflow or database CHECK constraint violations.
4. Stress-test cache invalidation on `GoiYMonAn` when new interactions are logged.
5. Stress-test guest/anonymous users accessing recommendations (no 401, no database foreign key violation).
6. Verify explainable tags match dish properties.

## Working Directory
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m4_1`

## Authoritative Inputs
- User Request: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` (Section R4 & Acceptance Criteria)
- Project Blueprint: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md`
- Worker Handoff: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_1/handoff.md`

## Deliverable
Deliver handoff report with empirical evidence and verdict (APPROVE or REQUEST_CHANGES) to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m4_1/handoff.md`

## 2026-10-14T16:12:54Z
Sender: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
Priority: MESSAGE_PRIORITY_HIGH
Content: You are Challenger m4_challenger_1 for Milestone 4 of Web App Nhà hàng Mộc.

Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m4_1

Read authoritative documents:
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_1/handoff.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m4_1/DISPATCH.md

Adversarial Focus:
1. Pure-Python TF-IDF & Cosine Similarity mathematical accuracy and edge cases.
2. Interaction weight correctness (xem=1, yeu_thich=2, them_gio_hang=3, dat_mon=4, danh_gia=5).
3. Cold-start popularity bounds in [0.0, 1.0] without Decimal overflow or CHECK constraint violation.
4. Cache invalidation on GoiYMonAn when user logs new interactions.
5. Guest/anonymous recommendations access without authentication error or database foreign key crash.
6. Run automated test suites and your own empirical tests.
7. Write your verdict (APPROVE or REQUEST_CHANGES) with empirical evidence to:
   /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m4_1/handoff.md
And notify the orchestrator via send_message.
