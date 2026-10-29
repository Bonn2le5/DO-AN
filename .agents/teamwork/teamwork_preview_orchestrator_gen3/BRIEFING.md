# BRIEFING — 2026-10-14T10:29:00Z

## Mission
Execute Milestone 3: Real-time Communication (Django Channels, ASGI, Redis Channel Layer, 2-Way Staff-Customer WebSocket Chat with DB persistence, Order FSM 6-State Transitions & Live Broadcast) for Web App Nhà hàng Mộc.

## 🔒 My Identity
- Archetype: teamwork_preview_orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen3
- Original parent: Sentinel
- Original parent conversation ID: 8dbae97e-f44b-48a7-a195-a69d53439dd6

## 🔒 My Workflow
- **Pattern**: Project Pattern (Greenfield/Modernization)
- **Scope document**: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen3/PROJECT.md
1. **Decompose**:
   - M1: Backend Schema Normalization & Migrations [DONE]
   - M2: VNPay Sandbox Deposit Payment & Table Concurrency Control [DONE]
   - M3: Real-time Communication (Channels & Redis) [IN_PROGRESS]
   - M4: AI Recommendation Engine & PostGIS GIS [PLANNED]
   - M5: Frontend Synchronization & Staff/Admin Portals [PLANNED]
   - M6: End-to-End Testing & Adversarial Hardening [PLANNED]
2. **Dispatch & Execute**:
   - Milestone 3 Iteration Loop: 3 Explorers (1 Spec Miner + 2 Explorers) -> 1 Worker -> 2 Reviewers + 2 Challengers + 1 Forensic Auditor -> Gate.
3. **On failure** (in this order):
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical, never auditor)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
4. **Succession**:
   - Self-succeed at 16 spawns after all subagents complete.
- **Current phase**: 2B (Iteration Loop for M3)
- **Current focus**: Milestone 3 Exploration (m3_spec_miner_1, m3_explorer_1, m3_explorer_2 running)

## 🔒 Key Constraints
- NEVER write, modify, or create source code files directly.
- NEVER run build/test commands yourself — require workers to do so.
- NEVER investigate or explore the problem at the code level — dispatch Explorers for technical investigation.
- File-editing tools are strictly permitted ONLY for metadata/state files (.md) in .agents/teamwork/.
- Forensic Auditor verdict is a BINARY VETO (CLEAN required).
- Never reuse a subagent after it has delivered its handoff — always spawn fresh.
- Always include ORIGINAL_REQUEST.md path in every dispatch.
- Always include mandatory integrity warning in Worker prompt.

## Current Parent
- Conversation ID: 8dbae97e-f44b-48a7-a195-a69d53439dd6
- Updated: 2026-10-14T10:29:00Z

## Key Decisions Made
- M1 & M2 passed all gates and forensic audits.
- Gen 3 takes over for M3: Channels, Redis Channel Layer, Chat Consumer with PostgreSQL persistence, Order FSM 6-state transitions with WebSocket broadcast.
- Dispatched 3 exploration agents for M3 on 2026-10-14T10:28Z.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|---|---|---|---|---|
| m3_spec_miner_1 | teamwork_preview_spec_miner | Milestone 3 WebSocket & FSM Specifications | in-progress | c6c45674-eb58-4c5b-9ef0-cbc390f35a51 |
| m3_explorer_1 | teamwork_preview_explorer | Milestone 3 Channels & ASGI Architecture | in-progress | b22c8ccd-e732-4248-baa2-9015c262bf2d |
| m3_explorer_2 | teamwork_preview_explorer | Milestone 3 Chat & Order FSM Implementation | in-progress | d75ca272-1d38-491d-886c-80d3d8c8fdba |

## Succession Status
- Succession required: no
- Spawn count: 3 / 16
- Pending subagents: c6c45674-eb58-4c5b-9ef0-cbc390f35a51, b22c8ccd-e732-4248-baa2-9015c262bf2d, d75ca272-1d38-491d-886c-80d3d8c8fdba
- Predecessor: teamwork_preview_orchestrator_gen2
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: 3b4ac039-b543-49a4-9b3d-21e996771d3e/task-380
- Safety timer: none

## Artifact Index
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md — Authoritative User Request
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen3/PROJECT.md — Global Project Blueprint
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen3/GATE_STATUS.md — Gate Verdict Matrix
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen3/progress.md — Liveness & Progress Log
- /Users/VuVan/Documents/DO-AN/TEST_INFRA.md — E2E Test Suite Specification
- /Users/VuVan/Documents/DO-AN/TEST_READY.md — E2E Test Readiness Verification
