# BRIEFING — 2026-10-14T15:58:00Z

## Mission
Investigate and architect Milestone 4 (Feature 23): PostGIS GIS Nearest Branch Spatial Query (ST_Distance, GiST spatial index, nearest branch API, and testing compatibility) for Web App Nhà hàng Mộc.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigation, synthesis
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_2
- Original parent: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
- Milestone: Milestone 4 (Feature 23: PostGIS Nearest Branch Spatial Query)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Deliver full 5-component handoff report (Observation, Logic Chain, Caveats, Conclusion, Verification Method) in handoff.md
- Use send_message to report to parent agent (e1a47f66-ae44-4e72-ae56-b7ecb23a0048)

## Current Parent
- Conversation ID: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
- Updated: 2026-10-14T15:57:23Z

## Investigation State
- **Explored paths**:
  - `moc_schema_tieng_viet.sql`: `chi_nhanh` table with `geography(Point, 4326)` and GiST index.
  - `moc-backend/branches/models.py`: `ChiNhanh` model, `PointFieldClass` fallback.
  - `moc-backend/branches/serializers.py`: `ChiNhanhSerializer` coordinate accessors.
  - `moc-backend/branches/views.py`: `BranchViewSet` and missing `nearest` actions.
  - `moc-backend/config/settings.py`: PostGIS vs SQLite database engine and GDAL/GEOS paths.
  - `moc-frontend/src/api/locations.api.ts`: API expectations for branches and coordinates.
  - `tests/e2e/tier1/test_t1_recommendation_gis.py` & `tests/e2e/helpers/ai_gis_oracle.py`: Haversine reference implementation.
- **Key findings**:
  - Missing GDAL/GEOS paths in `settings.py` causing `ImproperlyConfigured` on macOS Homebrew.
  - SQLite lacks spatial backend; executing `Distance()` triggers `TypeError: Distance function requires a GeometryField`.
  - Serializer crashes with `AttributeError: 'str' object has no attribute 'x'` when `toa_do_gis` is string without coordinate properties.
  - Haversine geodesic calculation provides exact math equivalence to PostGIS `ST_Distance(geography)` (<0.1% delta).
- **Unexplored areas**: None, full investigation complete.

## Key Decisions Made
- Architected clean Hybrid Spatial Pattern: PostGIS native query on PostgreSQL, automatic Haversine fallback on SQLite/testing.
- Standardized coordinate handling: `Point(x=lng, y=lat, srid=4326)` with string and tuple fallback parsing.
- Added GiST index via `GistIndex(fields=['toa_do_gis'], name='idx_chi_nhanh_toa_do')`.
- Designed dual REST API endpoints: `/api/branches/nearest/`, `/api/chi-nhanh/nearest/`, and `/api/chi-nhanh/tim-gan-nhat/`.

## Artifact Index
- DISPATCH.md — Initial dispatch tasks and status check updates
- BRIEFING.md — Working memory and context tracking
- progress.md — Liveness heartbeat and milestone tracking
- handoff.md — Authoritative 5-component handoff report and code blueprints
