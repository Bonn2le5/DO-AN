# Dispatch: Milestone 1 Implementation Worker

## Mandatory Integrity Warning
> DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Objective
Implement Milestone 1 (R1): Backend Model & DB Schema Normalization, Migration Regeneration, and Test Data Seeding.

## Mandatory Files to Read Before Starting
1. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` (Authoritative requirements)
2. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_1/PROJECT.md`
3. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_1/handoff.md` (Detailed models, aliases, properties, serializers, and admin recipes)
4. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_2/handoff.md` (Database setup, CheckConstraint fix `condition=` -> `check=`, clean migration sequence)
5. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_3/handoff.md` (Full implementation code for `seed_data.py`)
6. `/Users/VuVan/Documents/DO-AN/moc_schema_tieng_viet.sql`
7. `/Users/VuVan/Documents/DO-AN/Du-lieu-test.txt`

## Tasks & Write Ownership
You own all files in `moc-backend/` exclusively for this milestone:
1. **Model Normalization & Aliases (All 13 Apps)**:
   - Normalize models in `accounts`, `foods`, `branches`, `reservations`, `orders`, `payments`, `promotions`, `chat`, `recommendations`, `carts`, `reviews`, `posts`, `analytics` to Vietnamese canonical models matching `moc_schema_tieng_viet.sql`.
   - Provide backward-compatible model aliases in each `models.py` (`Food=MonAn`, `Order=DonHang`, `Branch=ChiNhanh`, `Payment=ThanhToan`, `Cart=GioHang`, `Review=DanhGia`, etc.).
   - Fix `CheckConstraint`: replace invalid `condition=` with `check=` in `orders/models.py`, `reservations/models.py`, `payments/models.py`.
   - Update `config/settings.py` (`AUTH_USER_MODEL = "accounts.NguoiDung"`).
   - Update `accounts/admin.py` to register `NguoiDung, VaiTro` with correct Vietnamese field names (`ten`, `mo_ta`).
   - Fix all views, serializers, and permissions (`api/permissions.py`) to eliminate all broken imports.
2. **Clean Migrations & DB Setup**:
   - Remove stale initial migrations from 2026-09-07 across all 13 apps (keep `__init__.py`).
   - Generate fresh migrations with `python manage.py makemigrations`.
   - Run `python manage.py check` to ensure 0 errors.
   - Run `python manage.py migrate` to apply migrations and establish the 36 Vietnamese tables.
3. **Data Seeder Command**:
   - Create `moc-backend/foods/management/commands/seed_data.py` (and `nap_du_lieu_mau.py`).
   - Implement the complete seeding logic from M1 Explorer 3 handoff: 5 categories, 100 dishes, 4 tags, 3 branches with PostGIS points, 22 tables, 20% deposit policy with 4 refund rules, and Admin/Staff/Customer user accounts.
   - Run `python manage.py seed_data` and verify records in the database.
4. **Verification**:
   - Run `python manage.py check` (must exit code 0).
   - Run `python tests/e2e/runner.py --tier 1` to verify Tier 1 test passes.
   - Document all verification commands and exact terminal outputs in your handoff report.

## Deliverables
Write your handoff report to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m1_1/handoff.md`
and notify Orchestrator via `send_message`.


## 2026-10-14T03:32:06Z
From: e7c4f174-4311-49a1-ac7b-15083103a212
You are Milestone 1 Implementation Worker for Web App Nhà hàng Mộc.
Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m1_1
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m1_1/DISPATCH.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your task:
Implement Milestone 1 (Backend Model & DB Schema Normalization, Migrations & Test Data Seed):
1. Normalize models in all 13 apps to Vietnamese schema with backward-compatible aliases, fix CheckConstraint (condition= -> check=), settings AUTH_USER_MODEL, admin.py, views.py, serializers.py, permissions.py.
2. Clean stale migrations and run makemigrations + migrate. Ensure `python manage.py check` passes with 0 errors.
3. Implement `foods/management/commands/seed_data.py` from M1 Explorer 3 handoff, run seed_data to load 100 dishes, categories, tags, branches, tables, deposit policy, users.
4. Run `python manage.py check` and `python tests/e2e/runner.py --tier 1`.
Document verification in /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m1_1/handoff.md and notify me via send_message when done.
