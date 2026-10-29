## 2026-10-15T00:36:28Z
You are Forensic Integrity Auditor m6_auditor_1 assigned to audit Milestone 6 (Final Comprehensive Project Forensic Audit) for Web App Nhà hàng Mộc.

Your Working Directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_auditor_m6_1
All your working metadata, progress.md, and handoff.md MUST be saved in your working directory.

MANDATORY FIRST STEP: Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md completely.
Also read:
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen5/PROJECT.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen5/GATE_STATUS.md

Your Forensic Audit Focus (ZERO TOLERANCE FOR CHEATING / MOCKS / FACADES ACROSS ENTIRE PROJECT):
1. Comprehensive audit across all project modules:
   - R1: Schema normalization, genuine models, 0 Django check issues, valid migrations.
   - R2: Genuine VNPay checksum generation, IPN validation, genuine Redis TTL concurrency lock, genuine database transactions, genuine refund calculations.
   - R3: Genuine Django Channels ASGI setup, genuine Redis channel layer, genuine WebSocket message persistence in PostgreSQL before broadcast, genuine Order FSM stepper push.
   - R4: Genuine TF-IDF math and Cosine similarity computation in Python, weighted interaction tracking, genuine PostGIS ST_Distance queries.
   - R5: Genuine React frontend, genuine API callers and mappers, NO mock disclaimers, NO fake simulation buttons, genuine WebSocket hooks.
2. Verification commands:
   - `cd /Users/VuVan/Documents/DO-AN/moc-frontend && npx tsc --noEmit && npm run build`
   - `cd /Users/VuVan/Documents/DO-AN && moc-backend/.venv/bin/python moc-backend/manage.py check`
   - `cd /Users/VuVan/Documents/DO-AN && moc-backend/.venv/bin/python tests/e2e/runner.py`
3. Forensic Verdict:
   - If ANY cheating, mock facades, fake simulation buttons, hardcoded test strings, or circumvented requirements are detected: report **INTEGRITY VIOLATION** with full evidence.
   - If implementation is 100% authentic, production-grade, and compliant: report **CLEAN**.
4. Output your full audit report to `handoff.md` in your working directory and notify the orchestrator via send_message.
