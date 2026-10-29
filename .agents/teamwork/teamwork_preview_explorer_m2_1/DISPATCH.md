# Dispatch: m2_explorer_1

## Task
You are Technical Explorer 1 for Milestone 2: 2-Phase Table Concurrency Control & BOM Deduction.

## Scope & Objective
Read:
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen2/PROJECT.md`
- `/Users/VuVan/Documents/DO-AN/moc-backend/reservations/` (models, views, serializers, urls)
- `/Users/VuVan/Documents/DO-AN/moc-backend/foods/` (models, views, inventory logic)
- `/Users/VuVan/Documents/DO-AN/moc-backend/config/settings.py` (Redis configuration, CACHES)

Investigate and provide technical design for:
1. Phase 1 Redis Temporary Hold:
   - Endpoint: `POST /api/tables/{id}/giu_ban/` and `/api/ban-an/{id}/giu_ban/`.
   - Redis key naming pattern: e.g. `table_hold:{table_id}:{date}:{slot/time}` or similar.
   - Concurrency lock: `SET key uuid NX EX 600` (10-minute TTL).
   - Collision detection: If key exists, return HTTP 409 Conflict with `{"detail": "Bàn này đang được người khác giữ chỗ hoặc đã được đặt", "code": "BAN_DANG_BAN"}`.
   - Hold token generation: UUIDv4 token returned to client (`id_giu_ban`).
2. Phase 2 DB Pessimistic Lock & Booking Confirmation:
   - Endpoint: `POST /api/reservations/` and `/api/dat-ban/`.
   - Atomic transaction `@transaction.atomic`.
   - Check if the reservation is backed by a valid hold token in Redis (or direct booking).
   - Pessimistic query: `BanAn.objects.select_for_update().get(id=ban_an_id)` and check for overlapping confirmed bookings.
   - Creation of `DatBan` record, deletion of Redis hold token.
3. Material Inventory Deduction (BOM):
   - When an order/reservation with dishes is confirmed: lookup `DinhMucNguyenLieu` for each dish.
   - Pessimistic lock `NguyenLieu.objects.select_for_update()`.
   - Check stock availability, deduct `so_luong_ton`, and create `LichSuXuatNhapKho` entry with type `xuat_kho` / `ban_hang`.

Deliver your findings and concrete implementation architecture in `handoff.md` in your directory (`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_1/handoff.md`).


## 2026-10-14T07:59:40Z
[Message] timestamp=2026-10-14T07:59:40Z sender=3b4ac039-b543-49a4-9b3d-21e996771d3e priority=MESSAGE_PRIORITY_HIGH
content=You are m2_explorer_1, Technical Explorer 1 for Milestone 2.
Your working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_1
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_1/DISPATCH.md
MANDATORY: Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen2/PROJECT.md before starting work.
Investigate and provide technical design for 2-Phase Table Concurrency Control (Phase 1 Redis SET NX EX 600 with HTTP 409, Phase 2 select_for_update() DB lock) and Material Inventory Deduction (BOM).
Write your complete findings and architecture to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_1/handoff.md and notify the caller when done.
