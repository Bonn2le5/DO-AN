# Dispatch: Channels & WebSocket Spec Miner (m3_spec_miner_1)

## Mission
Investigate and document precise specifications for Milestone 3 (Real-time Communication via Django Channels & Redis).

## Mandatory Inputs to Read
1. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
2. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen3/PROJECT.md`
3. `/Users/VuVan/Documents/DO-AN/moc_schema_tieng_viet.sql`
4. Existing models in `moc-backend/chat/models.py` and `moc-backend/orders/models.py`

## Specific Investigation Scope
1. **WebSocket Protocol & Message Schemas**:
   - 2-way Staff-Customer Chat (`/ws/chat/<conversation_id>/` or `/ws/chat/<hoi_thoai_id>/`):
     * Connection handshake, auth token passing (query parameter `?token=<jwt>` or headers).
     * Inbound message format (e.g. `{"action": "send_message", "message": "...", "sender_id": ...}` or `{"message": "..."}`).
     * Outbound broadcast message format (id, conversation_id, sender_id, sender_name, sender_role, noi_dung/content, thoi_gian_gui/timestamp, is_staff, etc.).
     * Typing indicator / read receipt schema if applicable.
   - Real-time Order Tracking (`/ws/orders/<order_id>/` and staff global order channel `/ws/orders/staff/`):
     * Outbound event schema for order status updates (`ma_don_hang`, `trang_thai_moi`, `trang_thai_cu`, `thoi_gian`, `ghi_chu`, `nhan_vien_thuc_hien`).
2. **Order FSM 6-State Transition Matrix**:
   - States: `cho_tiep_nhan` (Pending), `da_xac_nhan` (Confirmed), `dang_che_bien` (Cooking), `san_sang` (Ready), `hoan_tat` (Completed), `da_huy` (Cancelled).
   - Define exact allowable transitions:
     * `cho_tiep_nhan` -> `da_xac_nhan`, `da_huy`
     * `da_xac_nhan` -> `dang_che_bien`, `da_huy`
     * `dang_che_bien` -> `san_sang`, `da_huy`
     * `san_sang` -> `hoan_tat`, `da_huy`
     * `hoan_tat` -> [terminal, no transitions]
     * `da_huy` -> [terminal, no transitions]
   - Disallowed transitions (e.g., `cho_tiep_nhan` -> `hoan_tat` must raise validation error HTTP 400).
   - Side effects per transition (e.g. `da_xac_nhan` triggers BOM material deduction if not already deducted; `da_huy` triggers material refund if cooking not started; audit logging into `LichSuTrangThaiDon`).
3. **Redis Channel Layer Group Naming Conventions**:
   - Chat group: `chat_{conversation_id}`
   - Order specific group: `order_{order_id}`
   - Staff aggregate order group: `staff_orders`
   - Safe naming characters conforming to Channels regex rules (`[a-zA-Z0-9_.-]+`).

## Output Deliverable
Write your complete specification document to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m3_1/handoff.md`
and notify caller when complete.


## 2026-10-14T10:28:49Z
You are m3_spec_miner_1, the Channels & WebSocket Specification Miner for Milestone 3.
Your working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m3_1
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m3_1/DISPATCH.md
MANDATORY: Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen3/PROJECT.md before starting work.
Investigate and document precise specifications for:
1. WebSocket protocols & JSON message schemas for 2-way Staff-Customer Chat and Real-time Order Tracking.
2. 6-state Order FSM Transition Matrix (cho_tiep_nhan -> da_xac_nhan -> dang_che_bien -> san_sang -> hoan_tat / da_huy), allowed vs disallowed transitions, validation rules, side effects, and LichSuTrangThaiDon logging.
3. Redis Channel Layer group naming rules (chat_{conversation_id}, order_{order_id}, staff_orders) and Channels regex safety.
Write your complete specification report to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m3_1/handoff.md and notify the caller when done.
