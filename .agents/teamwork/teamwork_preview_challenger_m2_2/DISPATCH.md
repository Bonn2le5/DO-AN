# Dispatch: m2_challenger_2

## Task
You are Challenger 2 for Milestone 2: Concurrency Stress & BOM Race Condition Verification.

## Working Directory
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m2_2`

## MANDATORY READ
- Read `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- Read `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen2/PROJECT.md`
- Read `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m2_1/handoff.md`

## Challenge Objectives
1. Empirically verify 2-Phase Table Concurrency Control:
   - Concurrent hold requests: Simulate multiple threads attempting `giu_ban` on the exact same table and timeslot simultaneously. Exactly ONE thread must succeed (HTTP 200) and all other threads must receive HTTP 409 Conflict with `code: "BAN_DANG_BAN"`.
   - Concurrent booking confirmation: Simulate concurrent `tao_dat_ban` calls. Verify that table mutex (`BanAn` select_for_update) serializes the requests and prevents double booking.
   - Redis key expiration and token mismatch handling.
2. Empirically verify BOM Material Inventory Deduction under concurrent load:
   - Simulate concurrent orders with inverted ingredient requirements to verify that strict ascending ID ordering prevents deadlocks (`DeadlockDetected`).
   - Stock exhaustion: verify that when inventory is depleted, subsequent orders fail cleanly with `ValidationError` without partial deductions.
3. Write an empirical concurrent stress test script and execute it.
4. Formulate explicit verdict: **APPROVE** or **REQUEST_CHANGES**.

Write your handoff report to `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m2_2/handoff.md` and notify caller when done.


## 2026-10-14T08:39:23Z
You are m2_challenger_2, Challenger 2 for Milestone 2.
Your working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m2_2
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m2_2/DISPATCH.md
MANDATORY: Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m2_1/handoff.md.
Empirically stress test concurrent table holds (multi-threaded collision -> HTTP 409 BAN_DANG_BAN), concurrent booking confirmation, and concurrent BOM material deduction with deadlock prevention.
Deliver your report and verdict (APPROVE or REQUEST_CHANGES) in /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m2_2/handoff.md and notify the caller.
