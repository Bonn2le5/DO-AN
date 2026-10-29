# Dispatch: Milestone 1 Explorer 2 (Migrations & Database Setup Strategy)

## Mission
Analyze the migration dependencies, PostgreSQL/PostGIS database configuration, and sequence of migration generation for Milestone 1:
1. Examine the current status of PostgreSQL service on localhost:5432 and database `moc_db`. Identify how Postgres should be initialized/started if not running (e.g. `brew services start postgresql@14` or `pg_ctl`).
2. Identify existing stale migration files (from 2026-09-07) across all apps in `moc-backend/*/migrations/`.
3. Provide the exact clean migration strategy: cleaning old migrations, creating fresh `0001_initial.py` migrations in correct topological order to prevent circular foreign key issues (e.g. accounts -> foods -> branches -> reservations -> orders -> payments -> carts -> reviews -> chat -> recommendations -> analytics -> posts).
4. Verify PostGIS extension enablement (`CREATE EXTENSION IF NOT EXISTS postgis;`).
5. Ensure `python manage.py check` and `python manage.py migrate` pass 100% cleanly.

## Mandatory Files to Read
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_1/PROJECT.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_survey_1/handoff.md`

## Deliverables
Write your strategy report to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_2/handoff.md`
and notify Orchestrator via `send_message`.


## 2026-10-14T03:17:58Z
You are Milestone 1 Explorer 2 (Migrations & DB Setup Strategy) for Web App Nhà hàng Mộc.
Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_2
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_2/DISPATCH.md.
Investigate PostgreSQL service status, database moc_db setup, PostGIS extension, and migration dependency sequence across all 13 apps. Provide step-by-step strategy to make `python manage.py check` and `python manage.py migrate` pass 100%.
Write your report to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_2/handoff.md and notify me via send_message when done.
