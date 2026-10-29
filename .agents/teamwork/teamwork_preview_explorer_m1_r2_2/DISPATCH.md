# Dispatch: Milestone 1 Iteration 2 Explorer 2 (Registration, Auth Actions & Serializers)

## Mission
Analyze and provide the exact implementation fixes for the failures identified by Reviewer 1 and Challenger 1:
1. `DangKySerializer.create()` in `accounts/serializers.py`:
   - Fix the bug where `thu_dien_tu` was popped and not assigned to `NguoiDung.thu_dien_tu` (leaving it as empty string), which causes unique constraint violation on the 2nd user registration.
   - Ensure `thu_dien_tu` is properly set on `NguoiDung` instance (and synced with `email`).
2. `XacThucViewSet` in `accounts/views.py`:
   - Add explicit `@action` handlers for `register`, `profile`, and `change_password` (in addition to `dang_ky`, `ho_so`, `doi_mat_khau`) to support `moc-frontend/src/api/auth.api.ts` which calls `/api/auth/register/` and `/api/auth/profile/`.
3. Serializer payload compatibility:
   - Provide an input pre-processing hook (e.g. `to_internal_value`) on serializers so they transparently accept both English and Vietnamese payload keys (e.g. `email` -> `thu_dien_tu`, `name` -> `ten` / `ho_ten`, `price` -> `don_gia`).

## Mandatory Files to Read
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_1/PROJECT.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m1_1/handoff.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m1_1/handoff.md`

## Deliverables
Write your strategy report to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_2/handoff.md`
and notify Orchestrator via `send_message`.


## 2026-10-14T04:07:44Z
Sender: e7c4f174-4311-49a1-ac7b-15083103a212
Content: You are Milestone 1 Iteration 2 Explorer 2 (Registration, Auth Actions & Serializers) for Web App Nhà hàng Mộc.
Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_2
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_2/DISPATCH.md.
Analyze and provide complete strategy for fixing DangKySerializer.create() email bug, adding XacThucViewSet action aliases (register, profile, change_password), and serializer English payload input handling.
Write your report to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_2/handoff.md and notify me via send_message when done.
