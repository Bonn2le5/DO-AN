# BRIEFING — 2026-10-14T03:26:00Z

## Mission
Analyze all 13 Django apps models, serializers, views, admin, and settings to provide the complete strategy for standardizing to Vietnamese schema while maintaining backward-compatible aliases (Food=MonAn, etc.).

## 🔒 My Identity
- Archetype: explorer
- Roles: investigation, synthesis
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_1
- Original parent: e7c4f174-4311-49a1-ac7b-15083103a212
- Milestone: milestone-1

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Deliver complete strategy in handoff.md
- Cover all 13 Django apps, settings, admin, serializers, views

## Current Parent
- Conversation ID: e7c4f174-4311-49a1-ac7b-15083103a212
- Updated: 2026-10-14T03:26:00Z

## Investigation State
- **Explored paths**:
  - `moc-backend/config/settings.py` (AUTH_USER_MODEL = "accounts.User" -> "accounts.NguoiDung")
  - `moc-backend/api/` (permissions.py, urls.py)
  - All 13 apps (models, serializers, views, admin, services):
    `accounts`, `foods`, `branches`, `reservations`, `orders`, `payments`, `promotions`, `chat`, `recommendations`, `carts`, `reviews`, `posts`, `analytics`
  - `moc_schema_tieng_viet.sql` (36 tables, 17 enums)
  - `Du-lieu-test.txt`
- **Key findings**:
  1. `carts`, `reviews`, `posts`, `analytics` are still on legacy English models without `db_table` pointing to `moc_schema_tieng_viet.sql`.
  2. `accounts/admin.py` imports nonexistent `User, Role` and references nonexistent field names (`name`, `description`).
  3. `branches`, `payments`, `promotions`, `chat`, `recommendations` have Vietnamese models but English serializers and views importing legacy names.
  4. `reservations` and `orders` have bugs in `source` and `prefetch_related`: `items` / `food_items` vs `danh_sach_mon`.
  5. `config/settings.py` has `AUTH_USER_MODEL = "accounts.User"` which fails against `NguoiDung`.
  6. Two-layer adapter pattern (Model Aliases + Property Getters/Setters + Dual Serializers/Routers) guarantees 100% backward compatibility and 100% schema alignment with `moc_schema_tieng_viet.sql`.
- **Unexplored areas**: None for M1 scope; all 13 apps fully cataloged.

## Key Decisions Made
- Formulate complete code recipes with verbatim diffs/replacements for all 13 apps.
- Provide full 5-component handoff report.

## Artifact Index
- handoff.md — Complete Strategy Report for Models & Aliases
