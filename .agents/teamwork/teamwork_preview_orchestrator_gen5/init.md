# Initialization Context for Project Orchestrator Gen 5

## Project State
- **Project**: Web App Nhà hàng Mộc (Full-Stack Smart Restaurant Management & Food Ordering)
- **Authoritative Request**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- **Global Project Blueprint**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen5/PROJECT.md`
- **Predecessor Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4`

## Milestone Progression Summary
1. **Milestone 1 (R1 - Schema Normalization & Migrations)**: **100% COMPLETE & PASSED**
   - 0 errors on `python manage.py check`
   - Clean 0001_initial.py migrations across 13 apps
   - 18/18 adversarial tests pass
   - 30/30 Tier 1 E2E tests pass
   - Forensic Integrity Audit: CLEAN
2. **Milestone 2 (R2 - VNPay Sandbox & Table Concurrency Control)**: **100% COMPLETE & PASSED**
   - VNPay HMAC-SHA512 checksum, IPN webhook, Return URL
   - 2-Phase Concurrency Control (Phase 1 Redis hold 10m TTL `SET NX` returning 409; Phase 2 DB pessimistic lock `select_for_update()`)
   - Automated refund policy (>24h: 100%, 6-24h: 50%, <6h: 0%)
   - 5/5 verification squad unanimous approval (2 Reviewers, 2 Challengers with 50-thread race tests, 1 Forensic Auditor CLEAN)
3. **Milestone 3 (R3 - Real-Time Communication & Order FSM)**: **100% COMPLETE & PASSED**
   - Django Channels 4.3.2 + Redis Channel Layer (with in-memory fallback for test runners)
   - 2-way persistent WebSocket chat (`ChatConsumer`) linked to PostgreSQL `TinNhan` / `HoiThoai`
   - 6-state Order FSM (`cho_tiep_nhan` → `da_xac_nhan` → `dang_che_bien` → `san_sang` → `hoan_tat` / `da_huy`) with live group broadcasts and BOM stock deduction/restock hooks
   - 5/5 verification squad unanimous approval (2 Reviewers, 2 Challengers, 1 Forensic Auditor CLEAN)
4. **Milestone 4 (R4 - AI Recommendation Engine & PostGIS GIS)**: **100% COMPLETE & PASSED**
   - Content-Based Filtering with TF-IDF, Cosine Similarity, interaction weighting (order=6, review=5, cart=4, fav=3, view=1), cold-start popularity fallback, and explainable recommendations
   - PostGIS spatial querying with Haversine spherical math, antipodal clamping, GiST index support
   - Round 2 verification gate PASSED unanimously with clean forensic audit.
5. **Milestone 5 (R5 - Frontend Synchronization & Staff/Admin Portals)**: **IMPLEMENTATION COMPLETE, GATE VERIFICATION PENDING**
   - Worker `m5_worker_1` (`teamwork_preview_worker_m5_1/handoff.md`) completed all implementation:
     * `npm run build` & `npx tsc --noEmit`: 0 errors (Exit code 0)
     * `python manage.py check`: 0 issues
     * `python manage.py test recommendations branches chat orders reviews`: 58/58 PASS
     * `python tests/e2e/runner.py`: 60/60 PASS (100%)
     * TypeScript types, DTO mappers, WebSocket chat & order tracking hooks, table reservation floor plan, inventory & menu management, review moderation, staff live chat all implemented.
   - Verification Squad was spawned in Gen 4 right when quota limit was hit; subagents need to be freshly dispatched and evaluated.

## Immediate Action for Gen 5
1. Dispatch Milestone 5 Verification Squad:
   - Reviewer 1 (Frontend & API integration)
   - Reviewer 2 (Portals architecture)
   - Challenger 1 (WebSocket realtime stress)
   - Challenger 2 (Admin/Staff Portals integration stress)
   - Auditor 1 (Forensic integrity audit - binary veto, CLEAN required)
2. Evaluate Milestone 5 Gate upon receiving handoffs.
3. If Gate PASS, proceed to Milestone 6 (E2E Verification & Adversarial Hardening across R1-R5).
4. Run full test suites, adversarial suites, and ensure all acceptance criteria in `ORIGINAL_REQUEST.md` are 100% fulfilled.
5. Report completion to Sentinel so Sentinel can trigger the independent final victory audit.
