# BRIEFING — 2026-10-14T04:19:00Z

## Mission
Analyze and provide complete strategy for adding property setters, legacy kwargs mapping in model __init__, and Table/Order/Payment missing properties to fix Challenger 1 test failures.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigation, synthesis
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_1
- Original parent: e7c4f174-4311-49a1-ac7b-15083103a212
- Milestone: M1 Iteration 2

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Analyze and provide complete strategy for adding property setters, legacy kwargs mapping in model __init__, and Table/Order/Payment missing properties.

## Current Parent
- Conversation ID: e7c4f174-4311-49a1-ac7b-15083103a212
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `foods/models.py`, `branches/models.py`, `reservations/models.py`, `orders/models.py`, `payments/models.py`, `accounts/models.py`, `carts/models.py`, `reviews/models.py`, `promotions/models.py`, `chat/models.py`, `recommendations/models.py`, `analytics/models.py`, `posts/models.py`
  - Django `Model.__init__` execution path in `django.db.models.base`
- **Key findings**:
  - Confirmed 51+ properties lack `@<prop>.setter`, raising `AttributeError: can't set attribute` on assignment and instantiation.
  - Confirmed `BanAn` (`Table`) completely lacks `status`, `capacity`, `table_number`, `branch`, `area`, `Table.Status`.
  - Confirmed `DonHang` (`Order`) lacks `total` property.
  - Confirmed `ThanhToan` (`Payment`) lacks `amount`, `method`, `transaction_id`.
  - Confirmed `NguoiDung` (`User`) lacks `name`, `phone`.
  - Designed `LegacyKwargsMixin` to translate kwargs in `__init__` before Django field loop, ensuring 100% compatibility for `Model(**kwargs)` and `Model.objects.create(**kwargs)`.
- **Unexplored areas**: None. All 13 apps audited.

## Key Decisions Made
- Define `LegacyKwargsMixin` in `foods/models.py` as parent for `MoHinhThoiGian`, automatically endowing all 28 models across 12 apps with kwargs mapping and `created_at`/`updated_at` setters.
- For `accounts` models (`NguoiDung`, `VaiTro`, `QuyenHan`), inherit `LegacyKwargsMixin` directly.
- Add explicit `@property` and `@<prop>.setter` methods across all models for bidirectional property access.
- Add enum aliases `BanAn.Status = BanAn.TrangThaiBan = BanAn.TrangThai`.

## Artifact Index
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_1/handoff.md — Strategy report for Worker
