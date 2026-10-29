# BRIEFING — 2026-10-14T08:07:45Z

## Mission
Probe and document precise specifications for VNPay Sandbox 2.1.0 integration and Deposit Cancellation / Refund Policies.

## 🔒 My Identity
- Archetype: specification-miner
- Roles: Specification Miner
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m2_1
- Original parent: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Milestone: Milestone 2 (VNPay Sandbox & Deposit Refund Policy)

## 🔒 Key Constraints
- Investigate and document precise specifications for VNPay Sandbox 2.1.0 (params, HMAC-SHA512 checksum, IPN response codes, idempotency) and Deposit Cancellation / Refund Policies.
- Do NOT implement anything — read-only specification miner.
- All agent metadata stays strictly inside .agents/teamwork/teamwork_preview_spec_miner_m2_1.
- Write handoff.md and notify parent agent when done.

## Current Parent
- Conversation ID: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Updated: 2026-10-14T08:07:45Z

## Task Summary
- **What to build**: Specification documentation for VNPay Sandbox 2.1.0 and Deposit Cancellation / Refund Policy.
- **Success criteria**: Detailed, accurate handoff report with complete parameters, HMAC-SHA512 hashing algorithm, IPN return codes, idempotency rules, refund tier calculation, schema mappings, and verification procedures.
- **Interface contracts**: /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md, PROJECT.md
- **Code layout**: moc-backend (Django: payments, reservations apps)

## Key Decisions Made
- Fully probed VNPay v2.1.0 parameters (12 mandatory query params, HMAC-SHA512 checksum with ASCII sorted keys, quote_plus encoding).
- Verified IPN webhook 5-stage validation gatekeeper with response codes 00, 01, 02, 04, 97.
- Formalized Deposit Cancellation & Refund Policy: >24h (100%), 6-24h (50%), <6h (0%), no-show (0%).
- Designed PhieuHoanTien data structure and cancellation endpoint specifications with dual route support.
- Verified test suite compliance via Tier 1 and Tier 2 tests (100% passing).

## Artifact Index
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m2_1/handoff.md — Full specification report
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m2_1/progress.md — Progress tracker and liveness heartbeat
