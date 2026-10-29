# Dispatch: Milestone 1 Explorer 3 (Test Data Seeding Strategy)

## Mission
Analyze `Du-lieu-test.txt` and design the comprehensive Django management command (`seed_data.py` or `nap_du_lieu_mau.py`) for Milestone 1:
1. Parse `Du-lieu-test.txt` which contains 5 categories (`categories`), 100 dishes (`foods`) with `spicy_level`, `price`, `is_vegetarian`, `track_inventory`, and 4 tags (`tags`).
2. Map these SQL statements into Django ORM calls (`DanhMuc`, `MonAn`, `TheMonAn`).
3. Complete the missing test data required by Acceptance Criteria:
   - At least 3 restaurant branches (`ChiNhanh`) with realistic HCM/Hanoi coordinates as PostGIS `Point(lng, lat, srid=4326)`.
   - At least 20 restaurant tables (`BanAn`) across branches with various capacities (2, 4, 8, 12 seats) and initial status `trong`.
   - Default deposit policy (`ChinhSachDatCoc` with 20% deposit) and cancellation rules (`QuyTacHuyDatCoc`: >24h 100%, 6-24h 50%, <6h 0%).
   - Sample user accounts: Admin/Staff user (`admin@mocrestaurant.vn` / `staff@mocrestaurant.vn`) and sample customer (`khachhang@gmail.com`).
4. Ensure command is idempotent (`get_or_create`) and can be re-run safely.

## Mandatory Files to Read
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_1/PROJECT.md`
- `/Users/VuVan/Documents/DO-AN/Du-lieu-test.txt`
- `/Users/VuVan/Documents/DO-AN/moc_schema_tieng_viet.sql`

## Deliverables
Write your strategy report to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_3/handoff.md`
and notify Orchestrator via `send_message`.


## 2026-10-14T03:17:58Z
You are Milestone 1 Explorer 3 (Test Data Seeder Strategy) for Web App Nhà hàng Mộc.
Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_3
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_3/DISPATCH.md.
Analyze Du-lieu-test.txt and design the Django management command (seed_data.py) to populate categories, 100 foods, tags, plus required branches with PostGIS points, 20 tables with capacity, deposit policies, and test user accounts.
Write your report to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_3/handoff.md and notify me via send_message when done.
