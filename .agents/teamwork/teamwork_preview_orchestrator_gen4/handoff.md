# Orchestrator Soft Handoff (State Dump) — Gen 4 to Gen 5

- **Predecessor Orchestrator**: `teamwork_preview_orchestrator_gen4`
- **Predecessor Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4`
- **Parent Conversation ID**: `8dbae97e-f44b-48a7-a195-a69d53439dd6`
- **Date**: 2026-10-14T16:36:30Z
- **Target Successor**: Generation 5 Orchestrator (`teamwork_preview_orchestrator_gen5`)

---

## 1. Milestone State

| # | Milestone Name | Status | Key Outputs / Verdicts |
|---|---|:---:|---|
| M1 | Backend Schema Normalization & Migrations | **DONE** | 0 check issues, clean migrations, 30/30 Tier 1 E2E, 18/18 adversarial, CLEAN audit |
| M2 | VNPay Sandbox & Table Concurrency Control | **DONE** | VNPay HMAC-SHA512 checksum, IPN webhook, Redis SET NX 10m TTL + select_for_update, tiered refund, 51/51 M2 tests, 60/60 E2E, CLEAN audit |
| M3 | Real-Time Communication & Order FSM | **DONE** | Channels 4.3.2, SimpleJWT query string token, ChatConsumer atomic DB persistence before broadcast, 6-state Order FSM, BOM hooks, unanimous APPROVE & CLEAN audit |
| M4 | AI Recommendation Engine & PostGIS GIS | **IN_PROGRESS** (Remediation Ready) | Initial implementation complete (17/17 tests, 58/58 regression, 60/60 E2E). Reviewers 1 & 2 APPROVE. Challenger 2 APPROVE. Auditor CLEAN. Challenger 1 requested changes on 3 specific bugs. Round 2 Explorers have completed all investigations, drop-in patches, and verified solutions. Ready for Worker implementation! |
| M5 | Frontend Synchronization & Staff/Admin Portals | **PLANNED** | Types sync (`types/index.ts`), API alignment, Admin/Staff portals, WebSocket Chat & Tracking |
| M6 | End-to-End Full Verification & Hardening | **PLANNED** | Master test runner (Tiers 1-4 100%), Adversarial stress (Tier 5), Final Forensic Audit |

---

## 2. Active Subagents
- **Active Subagents Running**: None (All 17 subagents spawned by Gen 4 have completed their tasks and delivered reports).
- Cumulative Gen 4 Spawn Count: 17 / 16 (Succession Threshold Met).

---

## 3. Pending Decisions & Technical Context for Successor

### Milestone 4 Remediation Plan (Immediate Next Step for Gen 5)
Gen 5 starts with a fresh 0/16 spawn quota. The task at hand is fully architected and ready for Worker execution:

1. **Bug 1 (CRITICAL)**: `GoiYMonAnViewSet` in `moc-backend/recommendations/views.py` lacks `queryset` and `get_queryset()`, triggering HTTP 500 AssertionError on `GET /api/recommendations/<pk>/`.
   - **Fix Blueprint**: `m4_r2_explorer_1/handoff.md` (add `queryset = GoiYMonAn.objects.all()` and user-scoped `get_queryset()`).
   - Patch: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_1/patch_m4_remediation.patch`.

2. **Bug 2 (HIGH)**: `moc-backend/orders/services.py:83` had `trong_so=6` instead of `trong_so=4` on `DAT_MON`, violating Feature 20.
   - **Fix Blueprint**: `m4_r2_explorer_2/handoff.md` (change `trong_so=6` to `trong_so=4`).
   - Patch: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_2/remediation_bug2_orders_services.patch`.

3. **Bug 3 (MEDIUM)**: Cache invalidation on `GoiYMonAn` was only in `TuongTacMonAnViewSet`, so orders (`/api/orders/`) and reviews (`/api/reviews/`) failed to invalidate cache.
   - **Fix Blueprint**: `m4_r2_explorer_1/handoff.md` & `proposed_signals.py` (add `recommendations/signals.py` listening to `post_save` and `post_delete` on `TuongTacMonAn`, connect in `recommendations/apps.py:ready()`).

4. **GIS Hardening (from Challenger 2 & Explorer 3)**:
   - In `moc-backend/branches/services.py`: clamp `a = min(1.0, max(0.0, a))` to eliminate IEEE 754 antipodal float domain error.
   - In `moc-backend/branches/views.py`: sanitize `radius` and `limit` in `nearest` and `list` with `try...except ValueError` returning HTTP 400 Bad Request.
   - In `moc-backend/branches/views.py:list`: validate coordinates range `[-90, 90]` and `[-180, 180]`.
   - In `tests/e2e/helpers/ai_gis_oracle.py`: clamp `a`.
   - Fix Blueprints & Patches: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_3/` (`patch_services.patch`, `patch_views.patch`, `patch_ai_gis_oracle.patch`).

### Verification Commands for Successor:
1. `PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py` (Must transition from 3 FAIL to 3 PASS).
2. `PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_recommendations.py` (13/13 PASS).
3. `PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4.py` (18/18 PASS).
4. `moc-backend/.venv/bin/python moc-backend/manage.py test recommendations branches chat orders` (58/58 PASS).
5. `moc-backend/.venv/bin/python tests/e2e/runner.py` (60/60 PASS).

---

## 4. Remaining Work (Concrete Next Steps for Successor)

1. **Step 1 (Milestone 4 Worker)**: Spawn `m4_worker_2` (teamwork_preview_worker) with drop-in patches from `m4_r2_explorer_1`, `m4_r2_explorer_2`, and `m4_r2_explorer_3` to apply all fixes and run verification.
2. **Step 2 (Milestone 4 Verification Squad)**:
   - Spawn 2 Reviewers (`teamwork_preview_reviewer`)
   - Spawn 2 Challengers (`teamwork_preview_challenger`)
   - Spawn 1 Forensic Auditor (`teamwork_preview_auditor`)
3. **Step 3 (Milestone 4 Gate)**:
   - Verify all pass criteria. Mark Milestone 4 as **DONE** in `PROJECT.md` and `GATE_STATUS.md`.
4. **Step 4 (Milestone 5 Frontend Synchronization & Portals)**:
   - Decompose M5: Types synchronization (`moc-frontend/src/types/index.ts`), REST API endpoint alignment with backend, Admin/Staff portals (Table & Reservation, Menu & Inventory, Review Moderation, Staff Chat), and connecting `ChatWidget.tsx` and Order Tracking to Django Channels WebSockets.
   - Dispatch Explorers, Workers, Reviewers, Challengers, Auditor for Milestone 5.
5. **Step 5 (Milestone 6 E2E Full Integration & Final Hardening)**.

---

## 5. Key Artifacts
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` — Authoritative User Request
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md` — Global Project Blueprint
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/GATE_STATUS.md` — Gate Verdict Matrix
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_1/handoff.md` — Explorer R2-1 Report & Patch
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_2/handoff.md` — Explorer R2-2 Report & Feature 20 Audit
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_3/handoff.md` — Explorer R2-3 Report & GIS Blueprints
