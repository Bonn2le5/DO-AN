# BRIEFING — 2026-10-14T08:10:00Z

## Mission
Investigate and provide technical design for 2-Phase Table Concurrency Control (Phase 1 Redis SET NX EX 600 with HTTP 409, Phase 2 select_for_update() DB lock) and Material Inventory Deduction (BOM).

## 🔒 My Identity
- Archetype: explorer
- Roles: Technical Explorer 1 for Milestone 2
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_1
- Original parent: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Milestone: M2 - VNPay Sandbox & Table Concurrency Control

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Investigate backend implementation in moc-backend/reservations, moc-backend/foods, moc-backend/config
- Deliver technical design and findings in handoff.md
- Adhere to interface contracts in PROJECT.md

## Current Parent
- Conversation ID: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `moc-backend/config/settings.py` (CACHES configuration, Redis integration via Django 4.2 RedisCache)
  - `moc-backend/reservations/{models.py, views.py, serializers.py, services.py, admin.py}`
  - `moc-backend/foods/{models.py, views.py, serializers.py, admin.py, management/commands/seed_data.py}`
  - `moc-backend/orders/{models.py, views.py, services.py}`
  - `moc-backend/api/{urls.py, mixins.py}`
  - `moc-frontend/src/api/reservations.api.ts`
- **Key findings**:
  - Redis cache: Django 4.2 has built-in `django.core.cache.backends.redis.RedisCache`, `redis==7.0.1` installed in `.venv`.
  - Endpoint alignment: Frontend calls `POST /api/dat-ban/giu-ban/` while contract also specifies `POST /api/tables/{id}/giu_ban/` and `POST /api/ban-an/{id}/giu_ban/`. Dual support needed.
  - Phase 1 Redis hold: Needs normalized key `table_hold:{table_id}:{date}:{time}`, UUIDv4 token, collision check against both DB and Redis, returning HTTP 409 with `code: "BAN_DANG_BAN"`.
  - Phase 2 DB lock: Requires `@transaction.atomic` + `BanAn.objects.select_for_update().get(id=...)` to serialize concurrent requests, followed by Redis token verification and safe deletion.
  - BOM Deduction: Aggregates `DinhMucNguyenLieu` per dish, prevents deadlocks by sorting ingredient IDs before calling `NguyenLieu.objects.select_for_update()`, checks stock, deducts, and writes `LichSuXuatNhapKho`.
- **Unexplored areas**: None within scope.

## Key Decisions Made
- Architecture formulated for Phase 1 (Redis Hold), Phase 2 (Pessimistic Lock & DB check), and BOM Deduction with global resource ordering.
- Preserved dual-routing and payload compatibility for both backend contract and frontend callers.

## Artifact Index
- handoff.md — Comprehensive findings & architecture report
- progress.md — Liveness heartbeat and status log
