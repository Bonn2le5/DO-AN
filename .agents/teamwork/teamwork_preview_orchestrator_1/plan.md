# Orchestration Plan: Web App Nhà hàng Mộc

## Objective
Deliver a fully functional, high-integrity Smart Restaurant Management & Food Ordering system meeting all requirements (R1 to R5) and acceptance criteria in ORIGINAL_REQUEST.md.

## Phase 0: Survey & Scope Mapping
- Dispatch 3 exploratory agents (2 Explorers + 1 Spec Miner) in parallel:
  - **Explorer 1 (Backend & DB Schema)**: Examine `moc-backend`, Django apps, models, migrations, `moc_schema_tieng_viet.sql`, and `Du-lieu-test.txt`. Identify all model naming conflicts (`Food` vs `MonAn`, `Order` vs `DonHang`, etc.), migration failures, and seed data strategy.
  - **Explorer 2 (Frontend & Admin UI)**: Examine `moc-frontend` (Next.js/React TypeScript), routes, components, data mappers, API integration points, `ChatWidget.tsx`, admin/staff interfaces (Table/Reservation, Menu/Inventory, Reviews, Staff Chat).
  - **Spec Miner (Domain Specs & APIs)**: Analyze VNPay payment flow (HMAC-SHA512 checksum, IPN webhook, refund logic), Redis concurrency control (10m TTL reservation lock, pessimistic locking), Realtime FSM order states & WebSocket chat (Django Channels + Redis), AI recommendation (TF-IDF, Cosine Similarity, cold start, explainable tags), and PostGIS nearest branch query.
- Synthesize findings into `PROJECT.md` with full Architecture, Code Layout, Feature Inventory, and Milestones.

## Phase 1: Milestone Decomposition & Execution
- **Milestone 1 (R1)**: Backend Schema Normalization, Model Fixes, Migrations & Test Data Seed.
  - Acceptance: `python manage.py check` passes with 0 errors, migrations 100% applied, test data loaded (100+ foods, tables, branches, categories).
- **Milestone 2 (R2)**: VNPay Sandbox Deposit Payment & Table Concurrency Control.
  - Acceptance: 2-stage concurrency (Redis 10m TTL lock + pessimistic `select_for_update`), VNPay sandbox checkout URL generation, IPN webhook handling, refund policy automation (>24h 100%, 6-24h 50%, <6h 0%).
- **Milestone 3 (R3)**: Real-time Communication (WebSocket Chat & Order Status FSM).
  - Acceptance: Django Channels + ASGI + Redis Channel Layer. 2-way Staff-Customer chat with DB persistence. Real-time order state transition broadcast (`cho_tiep_nhan` -> `da_xac_nhan` -> `dang_che_bien` -> `san_sang` -> `hoan_tat`/`da_huy`).
- **Milestone 4 (R4)**: AI Recommendation Engine & GIS Nearest Branch.
  - Acceptance: Content-based filtering (TF-IDF + Cosine similarity), cold-start popularity fallback, explainable recommendation tags, PostGIS nearest branch query.
- **Milestone 5 (R5)**: Frontend Synchronization & Admin/Staff Portals.
  - Acceptance: Frontend API mapping synced 100% with backend, all admin views completed (Tables & Reservations, Menu & Inventory, Reviews, Staff Chat), `npm run build` passes with 0 TypeScript errors.
- **Milestone 6 (E2E & Hardening)**: Full E2E verification, integration testing, and adversarial coverage hardening.

## Quality & Integrity Gates
- Every milestone follows the strict cycle: Explorer -> Worker -> Reviewer(2) -> Challenger(2) -> Auditor(1) -> Gate.
- Forensic Auditor has binary veto: any integrity violation triggers an immediate rollback.
