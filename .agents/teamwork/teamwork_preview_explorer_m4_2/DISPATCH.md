# Dispatch Instructions for Explorer m4_explorer_gis

## Mission
Explore and design the technical blueprint for Milestone 4 (Feature 23): PostGIS GIS Nearest Branch Spatial Query (`ST_Distance`, GiST index, branch search API, distance calculation, and test compatibility).

## Working Directory
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_2`

## Authoritative Inputs
- User Request: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` (Section R4 & Acceptance Criteria)
- Project Blueprint: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md`
- Database Schema: `/Users/VuVan/Documents/DO-AN/moc_schema_tieng_viet.sql`
- Existing Backend Code: `moc-backend/branches/`, `moc-backend/config/settings.py`, `moc-backend/api/`
- Test Suites: `tests/e2e/tier1/`, `tests/e2e/tier2/`, `tests/e2e/runner.py`

## Exploration Tasks
1. Inspect `branches/models.py` (`ChiNhanh`), fields `vi_tri` (PointField, SRID 4326), `kinh_do`, `vi_do`, and PostGIS GiST index.
2. Investigate GDAL / GEOS / PostGIS library availability in `moc-backend/.venv` and environment (Mac OS, GDAL library paths in `settings.py`).
3. Investigate `ST_Distance` query: How is nearest branch queried using Django GIS ORM? (e.g. `ChiNhanh.objects.annotate(distance=Distance('vi_tri', user_point)).order_by('distance')`).
4. Investigate offline/SQLite test fallback: When testing with in-memory SQLite under `TESTING=True` without SpatiaLite, does Django GIS require spatialite or is there a fallback / math formula (`haversine` formula) when spatial backend is unavailable?
5. Investigate REST API endpoint: `/api/branches/nearest/` or `/api/branches/?lat=...&lng=...&radius=...`.
6. Inspect existing branch test cases in `tests/e2e/`.
7. Document all findings, edge cases, SQL queries, and verification commands in:
   `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_2/handoff.md`


## 2026-10-14T15:48:22Z
Sender: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
Priority: MESSAGE_PRIORITY_HIGH
Content:
You are Explorer m4_explorer_gis assigned to investigate and architect Milestone 4 (Feature 23): PostGIS GIS Nearest Branch Spatial Query (ST_Distance, GiST spatial index, nearest branch API, and testing compatibility) for Web App Nhà hàng Mộc.

Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_2

Read authoritative documents:
1. /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md (Section R4 & Acceptance Criteria)
2. /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md
3. /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_2/DISPATCH.md
4. /Users/VuVan/Documents/DO-AN/moc_schema_tieng_viet.sql

Key Investigation Objectives:
1. Review branches/models.py (ChiNhanh), spatial field vi_tri (PointField, SRID 4326), kinh_do, vi_do, and GiST index.
2. Check GDAL / GEOS / PostGIS library status in moc-backend/.venv and settings.py.
3. Specify exact ST_Distance query logic via Django GIS (from django.contrib.gis.db.models.functions import Distance; from django.contrib.gis.geos import Point).
4. Review testing compatibility: under SQLite testing without SpatiaLite, does Django GIS support fallback calculation (Haversine spherical distance formula)? Specify a clean hybrid approach so tests pass 100% on SQLite while PostGIS operates natively on PostgreSQL.
5. REST API endpoint specifications: /api/branches/nearest/?lat=...&lng=...&radius=... and /api/chi-nhanh/nearest/.
6. Deliver full 5-component handoff report (Observation, Logic Chain, Caveats, Conclusion, Verification Method) with concrete code blueprints to:
   /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_2/handoff.md
And notify orchestrator via send_message.


## 2026-10-14T15:57:23Z
Sender: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
Priority: MESSAGE_PRIORITY_HIGH
Content:
**Context**: Milestone 4 GIS Spatial Exploration Status Check
**Content**: Orchestrator checking in on your progress regarding PostGIS ST_Distance, ChiNhanh vi_tri spatial query, GiST indexing, nearest branch API endpoints, and SQLite fallback for tests. Please update your progress.md and compile your handoff report.
**Action**: Report your current findings and completion status.
