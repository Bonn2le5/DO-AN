# Dispatch Instructions for Challenger m3_challenger_2

## Mission
Adversarially and empirically stress-test Milestone 3: 6-State Order Finite State Machine (FSM), Concurrent Transitions, and BOM Inventory Side Effects.

## Working Directory
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m3_2`

## Authoritative Inputs
- User Request: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- Project Blueprint: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md`
- Worker Handoff: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m3_1/handoff.md`

## Adversarial Focus Areas
1. **6-State FSM Matrix & Strict Transition Rules**:
   - Verify every illegal transition raises `ValidationError` (skipping steps, reverse transitions, self-transitions, non-existent status strings).
   - Verify terminal states `hoan_tat` and `da_huy` are 100% immutable and cannot transition to anything.
2. **Actor & Authorization Enforcement**:
   - Customer can ONLY cancel (`da_huy`) an order if it is in `cho_tiep_nhan`.
   - Customer cannot cancel confirmed/cooking/ready orders.
   - Staff can execute all legal forward and cancellation transitions.
3. **Pessimistic Locking & Concurrency Race Stress**:
   - Concurrently trigger state transitions on the same order from multiple threads/coroutines -> verify exact one transition succeeds and no duplicate BOM deductions or state corruptions occur.
4. **BOM Material Inventory Deduction & Refund Hooks**:
   - Verify raw materials are deducted on `da_xac_nhan`.
   - Verify raw materials are refunded if cancelled from `da_xac_nhan` or `dang_che_bien`.
   - Verify no refund occurs if cancelled from `cho_tiep_nhan`.
5. **Execution & Report**:
   - Execute test suites and custom adversarial test scripts.
   - Report your verdict (APPROVE or REQUEST_CHANGES) with empirical evidence to:
     `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m3_2/handoff.md`
