# BRIEFING — 2026-10-14T10:38:00Z

## Mission
Investigate and document precise specifications for Milestone 3 (Real-time Communication via Django Channels & Redis), including Chat & Order Tracking WebSockets, 6-state Order FSM, and Redis Channel Layer group rules.

## 🔒 My Identity
- Archetype: specification miner
- Roles: external domain expert, spec miner
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m3_1
- Original parent: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Milestone: Milestone 3 (Real-time Communication via Django Channels & Redis)

## 🔒 Key Constraints
- Read-only probe: Do NOT implement anything.
- Discover and document features from authoritative sources.
- WebSocket protocols & JSON message schemas for 2-way Staff-Customer Chat and Real-time Order Tracking.
- 6-state Order FSM Transition Matrix (cho_tiep_nhan -> da_xac_nhan -> dang_che_bien -> san_sang -> hoan_tat / da_huy), allowed vs disallowed transitions, validation rules, side effects, and LichSuTrangThaiDon logging.
- Redis Channel Layer group naming rules (chat_{conversation_id}, order_{order_id}, staff_orders) and Channels regex safety.
- Write report to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m3_1/handoff.md.

## Current Parent
- Conversation ID: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Updated: 2026-10-14T10:38:00Z

## Task Summary
- **What to build**: Specification document for WebSocket protocols, 6-state Order FSM, and Redis Channel Layer groups.
- **Success criteria**: Comprehensive, verified specification with exact message schemas, FSM matrix, validation rules, side effects, and group naming conventions.
- **Interface contracts**: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen3/PROJECT.md
- **Code layout**: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen3/PROJECT.md

## Key Decisions Made
- Fully specified ASGI ProtocolTypeRouter and query-string JWT authentication middleware (`JWTAuthMiddleware`).
- Specified 2-way chat inbound frames (`send_message`, `typing`, `read_receipt`) and outbound frames (`chat_message`, `chat_typing`, `chat_read_receipt`, `error`).
- Specified real-time order tracking schemas for `/ws/orders/<order_id>/` and `/ws/orders/staff/`.
- Mapped out complete 6x6 Order FSM Transition Matrix with validation error format (HTTP 400), actor authorization, and BOM inventory deduction/refund side effects.
- Specified strict Channels group regex compliance (`^[a-zA-Z0-9_.-]+$`) and group naming rules (`chat_{id}`, `order_{id}`, `staff_orders`).
- Completed `handoff.md` with Features Discovered, Edge Cases, and 5-Component Handoff format.

## Artifact Index
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m3_1/handoff.md — Final specification report
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m3_1/progress.md — Liveness heartbeat
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m3_1/DISPATCH.md — Task assignment log
