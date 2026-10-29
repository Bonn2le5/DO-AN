# BRIEFING — 2026-10-14T04:18:00Z

## Mission
Analyze and provide complete strategy for fixing DangKySerializer.create() email bug, adding XacThucViewSet action aliases (register, profile, change_password), and serializer English payload input handling.

## 🔒 My Identity
- Archetype: explorer
- Roles: Explorer, Synthesizer
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_2
- Original parent: e7c4f174-4311-49a1-ac7b-15083103a212
- Milestone: Milestone 1 Iteration 2

## 🔒 Key Constraints
- Read-only investigation — do NOT implement directly in source code
- Analyze failures identified by Reviewer 1 and Challenger 1
- Provide complete strategy for DangKySerializer.create() bug, XacThucViewSet action aliases, serializer English payload input handling
- Write report to handoff.md in working directory
- Notify orchestrator via send_message when done

## Current Parent
- Conversation ID: e7c4f174-4311-49a1-ac7b-15083103a212
- Updated: 2026-10-14T04:18:00Z

## Investigation State
- **Explored paths**: accounts/serializers.py, accounts/models.py, accounts/views.py, api/urls.py, all 13 serializers across apps, moc-frontend/src/api/auth.api.ts, RegisterPage.tsx, LoginPage.tsx, authStore.ts, types/index.ts, tests/e2e/runner.py, test_t1_backend.py, test_t1_frontend.py.
- **Key findings**:
  1. `DangKySerializer.create()` line 51 calls `.pop("thu_dien_tu")`, leaving `thu_dien_tu=''` on user creation, causing duplicate key IntegrityError on 2nd user registration.
  2. `XacThucViewSet` only declares Vietnamese actions (`dang_ky`, `ho_so`, `doi_mat_khau`). Frontend `auth.api.ts` calls `/auth/register/` and `/auth/profile/`, resulting in 404s. In addition, response envelope must include `user` (for `mapUser(data.user)`) with `email`, `roles`, `is_restaurant_staff`. Also SimpleJWT login requires `thu_dien_tu` which fails when frontend passes `email`.
  3. DRF serializers strip English keys in `to_internal_value()` before `validate()` runs, rendering validation fallbacks dead code. `DualPayloadMixin` with `to_internal_value` mapping `FIELD_ALIASES` solves 100% of serializer bilingual input compatibility.
- **Unexplored areas**: None. All 3 target problem spaces thoroughly analyzed and verified with empirical test scripts.

## Key Decisions Made
- Formulated complete code-level strategy for `DangKySerializer.create()`, `NguoiDung.save()`, and `NguoiDung` name/phone property setters.
- Formulated complete routing and envelope strategy for `XacThucViewSet` (`register`, `profile`, `change_password`) and `DangNhapTokenSerializer`.
- Cataloged full field mapping table across all 13 serializers and verified `DualPayloadMixin` operation.
- Documented step-by-step verification methods for post-implementation audit.

## Artifact Index
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_2/handoff.md — Final analysis and strategy report
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_2/progress.md — Progress tracking
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_2/DISPATCH.md — Task log
