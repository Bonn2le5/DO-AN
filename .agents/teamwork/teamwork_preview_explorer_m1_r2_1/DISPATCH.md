# Dispatch: Milestone 1 Iteration 2 Explorer 1 (Property Setters & Legacy Kwargs)

## Mission
Analyze and provide the exact implementation fixes for the failures identified by Challenger 1:
1. Property setters missing on models:
   - Provide `@<property>.setter` for all legacy properties across models (`food.name`, `food.price`, `branch.name`, `order.status`, etc.) so that attribute assignment does not raise `AttributeError`.
2. Legacy kwargs instantiation:
   - Implement custom `__init__` on models or a metaclass/mixin that maps legacy English keyword arguments (`name`, `price`, `status`, `capacity`, `table_number`, `branch`, `area`) to the corresponding Vietnamese database fields (`ten`, `don_gia`, `trang_thai`, `suc_chua`, `so_ban`, `chi_nhanh`, `khu_vuc`).
3. Core model properties:
   - `Table`: ensure `status`, `capacity`, `table_number`, `branch`, `area`, and `Table.Status = BanAn.TrangThaiBan` exist and work.
   - `Order`: ensure `total` maps to `tong_tien`.
   - `User`: ensure `name` maps to `ho_ten` or `first_name`.
   - `Payment`: ensure `amount` maps to `so_tien`.

## Mandatory Files to Read
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_1/PROJECT.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m1_1/handoff.md` (Detailed failure report)
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m1_1/handoff.md`

## Deliverables
Write your strategy report to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_1/handoff.md`
and notify Orchestrator via `send_message`.

## 2026-10-14T04:07:44Z
You are Milestone 1 Iteration 2 Explorer 1 (Property Setters & Legacy Kwargs) for Web App Nhà hàng Mộc.
Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_1
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_1/DISPATCH.md.
Analyze and provide complete strategy for adding property setters, legacy kwargs mapping in model __init__, and Table/Order/Payment missing properties.
Write your report to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_1/handoff.md and notify me via send_message when done.
