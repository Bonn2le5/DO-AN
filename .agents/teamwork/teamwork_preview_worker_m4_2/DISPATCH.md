## 2026-10-14T16:38:24Z

# Dispatch: m4_worker_2

## Task
Implement Milestone 4 Remediation for Web App Nhà hàng Mộc based on the exact blueprints and patches produced by Explorers R2-1, R2-2, and R2-3.

## Working Directory
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_2`

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Authoritative Documents to Read:
1. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` (MANDATORY)
2. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md`
3. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_1/handoff.md` (Blueprints for Bug 1 & Bug 3)
4. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_2/handoff.md` (Blueprints for Bug 2 & Feature 20 audit)
5. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_3/handoff.md` (Blueprints for GIS edge cases)
6. Available drop-in files & patches:
   - `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_1/proposed_signals.py`
   - `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_1/patch_m4_remediation.patch`
   - `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_2/remediation_m4_all_bugs.patch`
   - `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_3/proposed_services.py`
   - `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_3/proposed_views.py`

## Implementation Steps:
1. `moc-backend/recommendations/views.py`:
   - Set `queryset = GoiYMonAn.objects.all()` on `GoiYMonAnViewSet`.
   - Implement `get_queryset(self)`: return `GoiYMonAn.objects.filter(nguoi_dung=user)...` if user is authenticated, else `GoiYMonAn.objects.none()`.
2. `moc-backend/recommendations/signals.py`:
   - Create `recommendations/signals.py` with `@receiver(post_save, sender=TuongTacMonAn)` and `@receiver(post_delete, sender=TuongTacMonAn)` to delete `GoiYMonAn` cache for `instance.nguoi_dung_id`.
3. `moc-backend/recommendations/apps.py`:
   - Add `ready(self)` method to import `recommendations.signals`.
4. `moc-backend/orders/services.py:83`:
   - Update `trong_so=6` to `trong_so=4` on `TuongTacMonAn.objects.create(...)`.
5. `moc-backend/branches/services.py`:
   - In `haversine_distance_km`: clamp `a = min(1.0, max(0.0, a))` to eliminate IEEE 754 antipodal float domain error.
6. `moc-backend/branches/views.py`:
   - In `nearest` and `list`: sanitize `radius` and `limit` with `try...except ValueError` returning HTTP 400 Bad Request.
   - In `list`: validate coordinates range `-90.0 <= lat_f <= 90.0` and `-180.0 <= lng_f <= 180.0` returning HTTP 400 Bad Request.
7. `tests/e2e/helpers/ai_gis_oracle.py`:
   - Clamp `a = min(1.0, max(0.0, a))` in `haversine_distance_km`.

## Verification Commands to Execute:
1. `moc-backend/.venv/bin/python moc-backend/manage.py check` (0 issues)
2. `PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py` (Must PASS 3/3 tests)
3. `PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_recommendations.py` (Must PASS 13/13 tests)
4. `PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4.py` (Must PASS 18/18 tests)
5. `moc-backend/.venv/bin/python moc-backend/manage.py test recommendations branches chat orders` (Must PASS 58/58 tests)
6. `moc-backend/.venv/bin/python tests/e2e/runner.py` (Must PASS 60/60 tests)

When finished, write your handoff report to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_2/handoff.md`
And notify the orchestrator via send_message.
