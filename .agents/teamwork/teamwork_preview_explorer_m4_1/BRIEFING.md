# BRIEFING — 2026-10-14T15:57:00Z

## Mission
Investigate and architect Milestone 4 (Features 19-22): Content-Based Food Recommendation Engine (TF-IDF & Cosine Similarity, Weighted User Interactions, Cold-Start Fallback, and Explainable Recommendation Tags) for Nhà hàng Mộc.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigation, synthesis
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1
- Original parent: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
- Milestone: Milestone 4 (Content-Based Recommendation Engine)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Deliver full 5-component handoff report (Observation, Logic Chain, Caveats, Conclusion, Verification Method) in handoff.md
- Maintain progress.md heartbeat

## Current Parent
- Conversation ID: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `moc-backend/.venv` (pip list analysis: scikit-learn, numpy, scipy absent, network offline)
  - `moc_schema_tieng_viet.sql` (tuong_tac_mon_an, goi_y_mon_an, mon_an, the_mon_an, nguyen_lieu)
  - `moc-backend/recommendations/` (models.py, services.py, views.py, serializers.py)
  - `moc-backend/foods/` (models.py, serializers.py)
  - `moc-backend/api/urls.py` (recommendation routing)
  - `tests/e2e/helpers/ai_gis_oracle.py`, `tests/e2e/tier1/test_t1_recommendation_gis.py`, `tests/e2e/tier4/test_t4_scenarios.py`
  - `moc-frontend/` (AIRecommendationSection.tsx, recommendations.api.ts, mappers.ts)
- **Key findings**:
  - `scikit-learn` & `numpy` are not installed and pip is offline; pure-Python TF-IDF and Cosine Similarity is strictly required.
  - Interaction weights in existing `services.py` were incorrect; standardized to: `xem=1, yeu_thich=2, them_gio_hang=3, dat_mon=4, danh_gia=5`.
  - Cold-start in existing `services.py` set score = `so_luot_danh_gia` which violated PostgreSQL CHECK constraint `[0, 1]`; resolved with normalized composite formula `0.6*(reviews/max) + 0.4*(rating/5.0)`.
  - Explainable tags defined for lẩu, cay, nướng/hải sản, chay, and cold-start.
  - Cache policy designed using `GoiYMonAn` table with invalidation on interaction and guest in-memory fallback.
- **Unexplored areas**: None. Complete blueprint delivered.

## Key Decisions Made
- Designed 100% Pure-Python TF-IDF and Cosine Similarity engine matching `math`, `re`, `collections`.
- Delivered full proposed files: `proposed_services.py`, `proposed_views.py`, `proposed_serializers.py`, `proposed_urls.py`, `proposed_tests.py`, and `test_algo.py`.
- Formatted and delivered full 5-component handoff report in `handoff.md`.

## Artifact Index
- DISPATCH.md — Dispatch instructions & log
- BRIEFING.md — Persistent context & situational awareness
- progress.md — Liveness heartbeat
- handoff.md — 5-component handoff report
- test_algo.py — Independent mathematical validation test
- proposed_services.py — Proposed pure-python recommendation service
- proposed_views.py — Proposed viewsets with guest cold-start & cache invalidation
- proposed_serializers.py — Proposed serializers with dual aliases & auto weighting
- proposed_urls.py — Proposed URL routes
- proposed_tests.py — Proposed Django unit test suite
