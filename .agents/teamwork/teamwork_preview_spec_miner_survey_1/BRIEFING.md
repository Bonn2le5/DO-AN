# BRIEFING — 2026-10-14T03:13:40Z

## Mission
Probe and document authoritative business logic specifications across VNPay, Concurrency Control, Realtime WebSocket/FSM, and AI Recommendation/PostGIS for Web App Nhà hàng Mộc.

## 🔒 My Identity
- Archetype: specification_miner
- Roles: Business Logic & Spec Miner
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_survey_1
- Original parent: e7c4f174-4311-49a1-ac7b-15083103a212
- Milestone: Survey & Specification Phase

## 🔒 Key Constraints
- Read-only probe: Do NOT implement anything — only discover, probe, and document specifications.
- Prioritize authoritative sources: schema SQL, prompt txt, reference docx/pages, backend codebase.
- Output comprehensive report to handoff.md with 5 components and required tables (Features Discovered, Edge Cases).
- All files in own directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_survey_1.

## Current Parent
- Conversation ID: e7c4f174-4311-49a1-ac7b-15083103a212
- Updated: 2026-10-14T03:13:40Z

## Task Summary
- **What to build**: Comprehensive Business Logic Specification for VNPay sandbox payment & refund, 2-phase concurrency control for reservation, Realtime FSM order states & WebSocket chat, AI recommendation (TF-IDF + Cosine) & PostGIS nearest branch.
- **Success criteria**: Detailed, unambiguous interface contracts, formulas, SQL queries, Redis key formats, HTTP status codes, error payloads, and edge cases documented. Completed in `handoff.md`.
- **Interface contracts**: /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md
- **Code layout**: moc-backend and moc-frontend

## Key Decisions Made
- Extracted authoritative requirements from `BB-V1_1250080238-DE-CUONG-DACN-CNPM - Vũ Nguyễn Văn.docx`, `moc_schema_tieng_viet.sql`, `prompt web nhà hàng .txt`, and current `moc-backend`/`moc-frontend`.
- Formulated exact mathematical equations and algorithms for TF-IDF cosine similarity, interaction weights, cold-start fallback, explainability heuristics, refund thresholds (>24h 100%, 6-24h 50%, <6h 0%), PostGIS spatial distance query with GiST index, Redis hold 600s TTL (SET NX), and DB pessimistic lock (`select_for_update`).

## Loaded Skills
- Source: None specified
- Local copy: None
- Core methodology: Specification mining via authoritative source extraction, boundary condition analysis, and concrete mathematical/data modeling.

## Artifact Index
- DISPATCH.md — Incoming assignment instructions
- BRIEFING.md — Persistent situational awareness
- progress.md — Task heartbeat and activity tracking
- handoff.md — Complete 5-component deliverable and specification report
