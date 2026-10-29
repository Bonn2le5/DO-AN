# BRIEFING — 2026-10-14T03:26:00Z

## Mission
Analyze Du-lieu-test.txt and design the Django management command (seed_data.py) to populate categories, 100 foods, tags, PostGIS branches, 20 tables, deposit policies, and test user accounts.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigation, synthesis
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_3
- Original parent: e7c4f174-4311-49a1-ac7b-15083103a212
- Milestone: Milestone 1

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Ensure command is idempotent (get_or_create) and re-runnable
- Map Vietnamese schema (moc_schema_tieng_viet.sql / Django models) accurately
- Integrate Du-lieu-test.txt (5 categories, 100 foods, 4 tags)
- Add required Acceptance Criteria data: 3 PostGIS branches, 20 tables with capacity, deposit policies, test user accounts

## Current Parent
- Conversation ID: e7c4f174-4311-49a1-ac7b-15083103a212
- Updated: 2026-10-14T03:26:00Z

## Investigation State
- **Explored paths**: Du-lieu-test.txt, moc_schema_tieng_viet.sql, moc-backend apps (foods, branches, reservations, accounts, orders, payments, promotions, carts, reviews), config/settings.py, .env, GeoDjango / GDAL paths.
- **Key findings**:
  1. `Du-lieu-test.txt` contains 5 categories, 100 dishes (20 per category), 4 tags. Regular expression parsing verified with 100% precision.
  2. Categories use fixed IDs in SQL (1..5) that must be safely mapped to `duong_dan` slugs ('lau', 'nuong', 'goi', 'nham-nhi', 'do-uong') to avoid auto-increment drift.
  3. GeoDjango Point takes `(longitude, latitude, srid=4326)`. Coordinates for 3 HCM branches verified.
  4. 22 tables designed across 3 branches covering 2, 4, 8, 12 seats with initial status 'trong'.
  5. Default deposit policy (20%, 10m hold, 15m payment) and 4 cancellation rules (>24h 100%, 6-24h 50%, <6h 0%, no-show 0%) mapped.
  6. RBAC roles ('quan_tri_vien', 'nhan_vien', 'khach_hang') and accounts ('admin@mocrestaurant.vn', 'staff@mocrestaurant.vn', 'khachhang@gmail.com') mapped.
  7. Value-add seeding for raw ingredients (BOM) and promotions prepared for M2/M4.
  8. Command placement targeted at `foods/management/commands/seed_data.py` (and alias `nap_du_lieu_mau.py`).
- **Unexplored areas**: None.

## Key Decisions Made
- Structured complete management command with auto-discovery file parser + embedded fallback.
- Added BOM and promotion seeding to unblock Milestone 2 directly.
- Guaranteed idempotency via `transaction.atomic` and `update_or_create` / `get_or_create`.

## Artifact Index
- DISPATCH.md — incoming instructions
- BRIEFING.md — working memory and identity
- progress.md — liveness heartbeat
- handoff.md — final analysis and strategy handoff report
