# Dispatch Instructions for Reviewer m4_reviewer_2

## Mission
Independently review Milestone 4 implementation (AI Recommendation Engine TF-IDF & Cosine Similarity, Interaction Weights, Cold-Start Fallback, Explainable Tags, and PostGIS GIS Nearest Branch Queries).

## Working Directory
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m4_2`

## Authoritative Inputs
- User Request: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` (Section R4 & Acceptance Criteria)
- Project Blueprint: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md`
- Worker Handoff: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_1/handoff.md`

## Review Tasks
1. Verify system check: `python moc-backend/manage.py check` (0 issues).
2. Verify unit and integration tests:
   - `python moc-backend/manage.py test recommendations branches`
   - `python moc-backend/manage.py test chat orders recommendations branches`
3. Verify E2E suites:
   - `python tests/e2e/runner.py --tier 1`
   - `python tests/e2e/runner.py --tier 4`
   - `python tests/e2e/runner.py`
4. Review code quality, security, and edge cases in:
   - `moc-backend/config/settings.py` (GDAL/GEOS auto-detection)
   - `moc-backend/recommendations/services.py` (Pure-Python TF-IDF, Cosine similarity, interaction weights, bounded cold-start, explainable tags, caching)
   - `moc-backend/recommendations/views.py`, `serializers.py`, `urls.py`
   - `moc-backend/branches/models.py`, `services.py`, `serializers.py`, `views.py`
5. Deliver handoff report with verdict (APPROVE or REQUEST_CHANGES) to:
   `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m4_2/handoff.md`


## 2026-10-14T16:12:54Z
You are Reviewer m4_reviewer_2 for Milestone 4 (AI Recommendations & PostGIS GIS) of Web App Nhà hàng Mộc.

Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m4_2

Read authoritative documents:
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_1/handoff.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m4_2/DISPATCH.md

Review Tasks:
1. Verify system check: python moc-backend/manage.py check
2. Verify unit and integration tests:
   - python moc-backend/manage.py test recommendations branches
   - python moc-backend/manage.py test chat orders recommendations branches
3. Verify master E2E runner:
   - python tests/e2e/runner.py --tier 1
   - python tests/e2e/runner.py --tier 4
   - python tests/e2e/runner.py
4. Conduct thorough code review on:
   - moc-backend/config/settings.py
   - moc-backend/recommendations/services.py, views.py, serializers.py, urls.py, tests.py
   - moc-backend/branches/models.py, services.py, serializers.py, views.py, tests.py
5. Write your complete handoff report with verdict (APPROVE or REQUEST_CHANGES) to:
   /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m4_2/handoff.md
And notify the orchestrator via send_message.
