# Dispatch Instructions for Explorer m4_explorer_ai

## Mission
Explore and design the technical blueprint for Milestone 4 (Feature 19-22): Content-Based Food Recommendation Engine (TF-IDF & Cosine Similarity, Weighted User Interactions, Cold-Start Fallback, and Explainable Recommendation Tags).

## Working Directory
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1`

## Authoritative Inputs
- User Request: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` (Section R4 & Acceptance Criteria)
- Project Blueprint: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md`
- Database Schema: `/Users/VuVan/Documents/DO-AN/moc_schema_tieng_viet.sql`
- Existing Backend Code: `moc-backend/recommendations/`, `moc-backend/foods/`, `moc-backend/api/`
- Test Suites: `tests/e2e/tier1/`, `tests/e2e/tier2/`, `tests/e2e/runner.py`

## Exploration Tasks
1. Inspect `recommendations/models.py` (`TuongTacMonAn`, `GoiYMonAn`), `foods/models.py` (`MonAn`, `DanhMuc`), and schema contracts.
2. Investigate feature vector extraction: What features are available for dishes? (Category name, ingredients in BOM, tags, spice level/mo_ta, name).
3. Investigate TF-IDF & Cosine Similarity implementation: Is scikit-learn installed in `moc-backend/.venv`? If not, what standard/pure-python or numpy/scipy implementations are available and supported offline?
4. Investigate interaction weights: `xem=1, thich=2, gio_hang=3, dat_hang=4, danh_gia=5`. How are interaction records created and aggregated into user preference profiles?
5. Investigate cold-start popularity fallback: How are popular dishes determined (e.g., aggregate orders/ratings or highest interaction counts) when user has 0 interactions?
6. Investigate explainable recommendation tags: Format and logic for returning explanations (e.g., "Gợi ý vì bạn đã thích [Món A]" or "Món lẩu cùng thể loại bạn yêu thích").
7. Investigate REST API endpoints: `/api/recommendations/` or `/api/foods/recommendations/` and response schema.
8. Document all findings, edge cases, formulas, and verification commands in:
   `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1/handoff.md`

## 2026-10-14T15:48:22Z
From sender=e1a47f66-ae44-4e72-ae56-b7ecb23a0048:
You are Explorer m4_explorer_ai assigned to investigate and architect Milestone 4 (Features 19-22): Content-Based Food Recommendation Engine (TF-IDF & Cosine Similarity, Weighted User Interactions, Cold-Start Fallback, and Explainable Recommendation Tags) for Web App Nhà hàng Mộc.

Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1

Read authoritative documents:
1. /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md (Section R4 & Acceptance Criteria)
2. /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md
3. /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1/DISPATCH.md
4. /Users/VuVan/Documents/DO-AN/moc_schema_tieng_viet.sql

Key Investigation Objectives:
1. Review recommendations/models.py (TuongTacMonAn, GoiYMonAn) and foods/models.py (MonAn, DanhMuc).
2. Check available packages in moc-backend/.venv (pip list): is scikit-learn, numpy, or scipy installed? If scikit-learn is absent and cannot be installed offline, specify a robust, pure-Python / numpy TF-IDF and Cosine Similarity implementation.
3. Interaction weighting formula: xem=1, thich=2, gio_hang=3, dat_hang=4, danh_gia=5. How user profiles are calculated from interactions.
4. Cold-start popularity fallback algorithm for users with 0 interactions (e.g. top ordered dishes or highest average rating).
5. Explainable recommendation tags: reasons provided to the customer ("Gợi ý cho bạn vì bạn đã thích [Món X]" or category match).
6. Cache strategy: GoiYMonAn table caching vs dynamic recalculation.
7. REST API endpoint specifications: /api/recommendations/ and /api/recommendations/tuong-tac/.
8. Deliver full 5-component handoff report (Observation, Logic Chain, Caveats, Conclusion, Verification Method) with concrete code blueprints to:
   /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1/handoff.md
And notify orchestrator via send_message.
