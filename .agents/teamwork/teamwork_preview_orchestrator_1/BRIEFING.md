# BRIEFING — 2026-10-14T04:44:00Z

## Mission
Lead the development, integration, and E2E verification of the Web App Nhà hàng Mộc project according to R1-R5 and acceptance criteria.

## 🔒 My Identity
- Archetype: teamwork_preview_orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_1
- Original parent: Sentinel
- Original parent conversation ID: 8dbae97e-f44b-48a7-a195-a69d53439dd6

## 🔒 My Workflow
- **Pattern**: Project
- **Scope document**: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_1/PROJECT.md
1. **Decompose**: Survey codebase & specs with Explorers, build Feature Inventory & Milestones in PROJECT.md.
2. **Dispatch & Execute** (pick ONE):
   - **Direct (iteration loop)**: For each milestone, run Explorer(3) -> Worker(1) -> Reviewer(2) -> Challenger(2) -> Auditor(1) -> Gate.
3. **On failure** (in this order):
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
   - Escalate: report to parent (last resort)
4. **Succession**: At 16 spawns, write handoff.md, cancel crons, spawn successor.
- **Work items**:
  1. Survey & Feature Inventory [done]
  2. Milestone Decomposition & Architecture (PROJECT.md) [done]
  3. Milestone 1: Backend Model & DB Schema Normalization (R1) [in-progress - Iteration 2 Gate Active]
  4. Milestone 2: VNPay Sandbox & Concurrency Control (R2) [pending]
  5. Milestone 3: Realtime Communication (Channels + Redis) (R3) [pending]
  6. Milestone 4: AI Recommendations & GIS Nearest Branch (R4) [pending]
  7. Milestone 5: Frontend Integration & Staff Admin (R5) [pending]
  8. Milestone 6: E2E Verification & Adversarial Coverage [pending]
- **Current phase**: Milestone 1 Iteration 2 Gate Evaluation
- **Current focus**: 5 verification agents (2 Reviewers, 2 Challengers, 1 Auditor) evaluating M1 Iteration 2 fixes.

## 🔒 Key Constraints
- NEVER write, modify, or create source code files directly.
- NEVER run build/test commands yourself — require workers to do so.
- NEVER investigate or explore the problem at the code level — dispatch Explorers for technical investigation.
- You MAY use file-editing tools ONLY for metadata/state files (.md) in your .agents/teamwork/ folder.
- Always include path to ORIGINAL_REQUEST.md in every subagent dispatch.
- Mandatory integrity warning in Worker dispatch.
- Audit verdict is a binary veto.
- Never reuse a subagent after it has delivered its handoff — always spawn fresh.

## Current Parent
- Conversation ID: 8dbae97e-f44b-48a7-a195-a69d53439dd6
- Updated: 2026-10-14T03:04:20Z

## Key Decisions Made
- Milestone 1 Iteration 2 implemented by Worker `d5a00465-1c58-4940-9b91-f797edd73687` with:
  - 0 issues in Django check
  - 21 models registered in admin
  - 18/18 passing in adversarial challenger suite
  - 30/30 passing in Tier 1 suite.
- Dispatched 5 verification subagents for Iteration 2 Gate.

## Active Timers
- Heartbeat cron: e7c4f174-4311-49a1-ac7b-15083103a212/task-279
- Safety timer: none (handled by heartbeat cron)
- On context truncation: run `manage_task(Action="list")` — re-create if missing

## Artifact Index
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md — Authoritative User Request
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_1/PROJECT.md — Global Project Specification
- /Users/VuVan/Documents/DO-AN/TEST_INFRA.md — E2E Test Infrastructure
- /Users/VuVan/Documents/DO-AN/TEST_READY.md — E2E Test Suite Sign-off Report
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_1/GATE_STATUS.md — Gate Verdict Matrix
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_1/DISPATCH.md — Parent Dispatch Record
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_1/BRIEFING.md — Persistent Working Memory
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_1/plan.md — Project Orchestration Plan
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_1/progress.md — Execution Progress & Heartbeat
