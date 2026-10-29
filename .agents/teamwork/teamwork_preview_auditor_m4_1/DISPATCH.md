# Dispatch Instructions for Forensic Auditor m4_auditor_1

## Mission
Perform comprehensive forensic integrity audit for Milestone 4 (AI Recommendation Engine & PostGIS GIS Spatial Queries).

## Working Directory
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_auditor_m4_1`

## Authoritative Inputs
- User Request: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` (Section R4 & Acceptance Criteria)
- Project Blueprint: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md`
- Worker Handoff: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_1/handoff.md`

## Forensic Audit Protocol & Verification
1. **Anti-Cheat / Anti-Facade Verification**:
   - Inspect `moc-backend/recommendations/services.py`, `views.py`, `serializers.py`.
   - Inspect `moc-backend/branches/models.py`, `services.py`, `serializers.py`, `views.py`.
   - Verify that recommendation outputs, similarity scores, and distances are genuinely computed dynamically from database objects and query coordinates, NOT hardcoded from test fixtures or canned lists.
2. **Mathematical Authenticity**:
   - Verify genuine TF-IDF calculation (Sublinear TF, smoothed IDF, L2 unit vector normalization).
   - Verify genuine Cosine Similarity dot product.
   - Verify genuine Haversine spherical distance trigonometry.
3. **Database & Schema Authenticity**:
   - Verify interaction records are genuinely written to `tuong_tac_mon_an`.
   - Verify recommendations are genuinely cached in `goi_y_mon_an`.
   - Verify score values conform to PostgreSQL `CHECK (diem_tuong_dong BETWEEN 0 AND 1)`.
4. **Deliverable**:
   - Deliver binary verdict: **CLEAN** or **INTEGRITY VIOLATION**.
   - Output full evidence report to:
     `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_auditor_m4_1/handoff.md`


## 2026-10-14T16:12:54Z
Received from orchestrator (e1a47f66-ae44-4e72-ae56-b7ecb23a0048):
You are Forensic Integrity Auditor m4_auditor_1 for Milestone 4 of Web App Nhà hàng Mộc.

Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_auditor_m4_1

Read authoritative documents:
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_1/handoff.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_auditor_m4_1/DISPATCH.md

Forensic Audit Verification:
1. Verify zero hardcoded results, dummy facades, or mock bypasses in recommendations/ and branches/.
2. Verify genuine TF-IDF and Cosine similarity math dynamically computed from database records.
3. Verify genuine Haversine spherical distance trigonometry.
4. Verify database persistence in tuong_tac_mon_an and goi_y_mon_an conforming to PostgreSQL CHECK constraints.
5. Provide a binary verdict: CLEAN or INTEGRITY VIOLATION.
6. Write your complete forensic audit report to:
   /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_auditor_m4_1/handoff.md
And notify the orchestrator via send_message.
