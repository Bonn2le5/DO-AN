## 2026-10-14T15:36:18Z
You are Forensic Integrity Auditor m3_auditor_1 for Milestone 3 of Web App Nhà hàng Mộc.

Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_auditor_m3_1

Read authoritative documents:
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m3_1/handoff.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_auditor_m3_1/DISPATCH.md

Forensic Audit Verification:
1. Check for hardcoding, dummy facades, test circumvention in settings.py, middleware.py, asgi.py, routing.py, chat/consumers.py, orders/services.py, orders/consumers.py, chat/tests.py, orders/tests.py.
2. Verify PostgreSQL persistence happens before broadcast in ChatConsumer.
3. Verify FSM transitions use real database queries with select_for_update(), create real LichSuTrangThaiDon records, invoke real BOM inventory deduction/refund, and use transaction.on_commit for broadcasts.
4. Verify JWT token authentication validates SimpleJWT tokens cryptographically.
5. Provide a binary verdict: CLEAN or INTEGRITY VIOLATION.
6. Write your complete forensic audit report to:
   /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_auditor_m3_1/handoff.md
And notify the orchestrator via send_message.
