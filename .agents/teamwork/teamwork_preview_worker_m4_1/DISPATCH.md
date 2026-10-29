# Dispatch Instructions for Worker m4_worker_1

## Mission
Implement Milestone 4:
1. **AI Recommendation Engine (Features 19–22)**: Content-Based Filtering using pure-Python TF-IDF and Cosine Similarity, interaction weights (`xem=1, yeu_thich=2, them_gio_hang=3, dat_mon=4, danh_gia=5`), cold-start popularity fallback bounded in [0.0, 1.0], explainable tags, caching on `GoiYMonAn`, cache invalidation, and REST API.
2. **PostGIS GIS Nearest Branch Queries (Feature 23)**: `ST_Distance` spatial queries on `ChiNhanh.vi_tri` with GiST index, hybrid Haversine geodesic fallback for SQLite testing, GDAL/GEOS library auto-detection, and nearest branch REST endpoints (`/api/branches/nearest/`, `/api/chi-nhanh/nearest/`).

## Working Directory
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_1`

## Authoritative Inputs & Blueprints
- User Request: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` (Section R4 & Acceptance Criteria)
- Project Blueprint: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md`
- AI Explorer Blueprint & Code Artifacts:
  - `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1/handoff.md`
  - `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1/proposed_services.py`
  - `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1/proposed_views.py`
  - `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1/proposed_serializers.py`
  - `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1/proposed_urls.py`
  - `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1/proposed_tests.py`
- GIS Explorer Blueprint:
  - `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_2/handoff.md`

## Files You Own Exclusively
- `moc-backend/config/settings.py` (GDAL & GEOS library auto-detection)
- `moc-backend/recommendations/services.py` (Pure-Python TF-IDF & Cosine Engine)
- `moc-backend/recommendations/views.py` (AllowAny recommendations, guest cold-start, refresh, interaction tracking)
- `moc-backend/recommendations/serializers.py` (Dual language aliases, auto-weight assignment)
- `moc-backend/recommendations/urls.py` (recommendation routes)
- `moc-backend/recommendations/tests.py` (recommendation unit & integration tests)
- `moc-backend/branches/models.py` (coordinate properties, string coordinate parser, GiST index)
- `moc-backend/branches/services.py` (find_nearest_branches with PostGIS ST_Distance & Haversine fallback)
- `moc-backend/branches/serializers.py` (distance annotations and coordinate accessors)
- `moc-backend/branches/views.py` (proximity sorting in list, nearest and tim-gan-nhat actions)
- `moc-backend/branches/tests.py` (branch spatial unit & integration tests)
- `moc-backend/api/urls.py` (router registrations for recommendations and branches)

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Completion Criteria
1. `python moc-backend/manage.py check` passes with 0 errors.
2. `python moc-backend/manage.py test recommendations branches` passes 100%.
3. `python moc-backend/manage.py test chat orders recommendations branches` passes 100%.
4. `python tests/e2e/runner.py --tier 1` and `python tests/e2e/runner.py --tier 4` pass 100%.
5. `python tests/e2e/runner.py` passes 60/60 tests (100% pass rate).
6. Write full handoff report to `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_1/handoff.md`.

## 2026-10-14T15:59:17Z
You are Worker m4_worker_1 assigned to implement Milestone 4 (AI Recommendation Engine & PostGIS GIS Spatial Queries) for Web App Nhà hàng Mộc.

Your working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_1

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Authoritative Documents & Blueprints to Read:
1. /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md (Section R4 & Acceptance Criteria)
2. /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md
3. /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_1/DISPATCH.md
4. /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1/handoff.md
5. Drop-in code files in /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1/:
   - proposed_services.py
   - proposed_views.py
   - proposed_serializers.py
   - proposed_urls.py
   - proposed_tests.py
6. /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_2/handoff.md (Blueprints 1 through 6)
