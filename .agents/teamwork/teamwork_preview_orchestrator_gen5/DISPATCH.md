# Dispatch: Generation 5 Project Orchestrator

## Mission
Resume orchestration of Web App Nhà hàng Mộc as Generation 5 Project Orchestrator.
Immediate focus: Execute Milestone 4 Remediation (Worker implementation of drop-in blueprints from Explorers R2-1, R2-2, R2-3) followed by Milestone 4 Verification Squad (2 Reviewers, 2 Challengers, 1 Forensic Auditor). Upon Milestone 4 Gate passing, advance to Milestone 5 (Frontend Synchronization & Portals) and Milestone 6 (E2E Full Verification).

## Parent Identification (MANDATORY)
- Your parent is `8dbae97e-f44b-48a7-a195-a69d53439dd6` — use this ID for all escalation and status reporting (send_message).
- Do NOT report to Gen 4 (which is terminated upon succession).

## Authoritative Documents to Read Immediately
1. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` (MANDATORY)
2. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md`
3. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/GATE_STATUS.md`
4. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/handoff.md` (Soft handoff with full state and next steps)
5. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/progress.md`
6. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_1/handoff.md` (Blueprints & patch for Bug 1 & Bug 3)
7. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_2/handoff.md` (Blueprints & patch for Bug 2)
8. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_3/handoff.md` (Blueprints & patch for GIS edge cases)
9. `/Users/VuVan/Documents/DO-AN/tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py` (Challenger 1 bug reproduction harness)

## Concrete Next Steps
1. Copy `PROJECT.md` and `GATE_STATUS.md` to your working directory `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen5/` and initialize `BRIEFING.md` and `progress.md`.
2. Start heartbeat cron `schedule(CronExpression="*/10 * * * *", Prompt="...")`.
3. Spawn `m4_worker_2` (teamwork_preview_worker) with drop-in patches from R2 Explorers to implement:
   - `recommendations/views.py`: `queryset = GoiYMonAn.objects.all()` and user-scoped `get_queryset()`.
   - `recommendations/signals.py`: `@receiver(post_save/post_delete, sender=TuongTacMonAn)` deleting `GoiYMonAn` cache, registered in `recommendations/apps.py:ready()`.
   - `orders/services.py:83`: `trong_so=4`.
   - `branches/services.py`: clamp `a = min(1.0, max(0.0, a))`.
   - `branches/views.py`: parameter sanitization for `radius` & `limit` and coordinate boundary checking in `list()`.
   - Run verification commands:
     * `manage.py check`
     * `tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py` (3/3 PASS)
     * `tests/e2e/test_adversarial_challenger_m4_recommendations.py` (13/13 PASS)
     * `tests/e2e/test_adversarial_challenger_m4.py` (18/18 PASS)
     * `manage.py test recommendations branches chat orders` (58/58 PASS)
     * `tests/e2e/runner.py` (60/60 PASS)
4. Dispatch Milestone 4 Verification Squad (2 Reviewers, 2 Challengers, 1 Forensic Auditor).
5. Gate Milestone 4 and advance to Milestone 5.


## 2026-10-14T23:46:57Z

[Message from Parent 8dbae97e-f44b-48a7-a195-a69d53439dd6]
Project Status & Context:
1. Milestone 1 (R1 - Backend & Schema Normalization) is 100% COMPLETE & VERIFIED (PASS).
2. Milestone 2 (R2 - VNPay Sandbox & Table Concurrency Control) is 100% COMPLETE & VERIFIED (PASS).
3. Milestone 3 (R3 - Real-Time Communication & Order FSM) is 100% COMPLETE & VERIFIED (PASS).
4. Milestone 4 (R4 - AI Recommendation Engine & PostGIS GIS) is 100% COMPLETE & VERIFIED (PASS).
5. Milestone 5 (R5 - Frontend Synchronization & Staff/Admin Portals) has been fully IMPLEMENTED by Worker m5_worker_1:
   - `npm run build` & `npx tsc --noEmit`: 0 errors (Exit code 0)
   - `python manage.py check`: 0 issues
   - `python manage.py test recommendations branches chat orders reviews`: 58/58 PASS
   - `python tests/e2e/runner.py`: 60/60 PASS (100%)
   - All components, portals, and WebSocket hooks implemented (handoff at /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m5_1/handoff.md).

Immediate Instructions:
1. Initialize your BRIEFING.md and progress.md in your working directory.
2. Read the worker handoff (`teamwork_preview_worker_m5_1/handoff.md`).
3. Dispatch the Milestone 5 Verification Squad:
   - 2 Reviewers (Frontend & API alignment, Portals architecture)
   - 2 Challengers (WebSocket stress, Portals integration stress)
   - 1 Forensic Integrity Auditor (Zero mock/facade check, genuine code verification)
4. Evaluate Milestone 5 Gate.
5. Upon Gate PASS, advance to Milestone 6 (E2E Verification & Adversarial Hardening):
   - Run the full suite of end-to-end integration tests covering all requirements (R1 through R5).
   - Ensure all acceptance criteria in ORIGINAL_REQUEST.md are completely satisfied.
6. When Milestone 6 passes, report project completion to the Sentinel so the Sentinel can trigger the independent final victory audit.
7. Keep progress.md and BRIEFING.md regularly updated.
