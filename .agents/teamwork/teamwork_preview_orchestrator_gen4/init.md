# Initialization Context for Project Orchestrator Gen 4

## Project State
- **Project**: Web App Nhà hàng Mộc (Full-Stack Smart Restaurant Management)
- **Authoritative Request**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- **Global Project Blueprint**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen3/PROJECT.md`
- **Predecessor Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen3`

## Milestone Progression
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
3. **Milestone 3 (R3 - Real-Time Communication & Order FSM)**: **IN PROGRESS (Exploration Complete)**
   - All 3 exploration handoffs are completed and available:
     * `teamwork_preview_spec_miner_m3_1/handoff.md`: WebSocket JSON frame schemas, 6-state Order FSM matrix, Redis group naming standards (`chat_{conversation_id}`, `order_{order_id}`, `orders_staff`).
     * `teamwork_preview_explorer_m3_1/handoff.md`: Channels 4.3.2 installed, `daphne` absent (offline sandbox constraint), `config/asgi.py` ProtocolTypeRouter blueprint, JWT query authentication middleware, channel layer configuration with in-memory fallback.
     * `teamwork_preview_explorer_m3_2/handoff.md`: Persistent `ChatConsumer` integration with `TinNhan` model, Order FSM transition validation & hooks in `orders/services.py`, dual viewset routing, and comprehensive test harness.

## Immediate Action for Gen 4
1. Synthesize the findings from the 3 exploration handoffs.
2. Dispatch `m3_worker_1` (`teamwork_preview_worker`) with the synthesized specification and test requirements.
3. Supervise implementation and run tests.
4. Dispatch Milestone 3 Verification Squad (2 reviewers, 2 challengers, 1 forensic integrity auditor).
5. Advance to Milestone 4 (AI Recommendation & GIS) upon Milestone 3 Gate PASS.
