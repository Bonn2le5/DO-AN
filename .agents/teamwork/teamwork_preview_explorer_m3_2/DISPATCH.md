# Dispatch: Chat & Order FSM Implementation Explorer (m3_explorer_2)

## Mission
Investigate and design the Chat WebSocket Consumer and Order FSM lifecycle transition implementation for Milestone 3.

## Mandatory Inputs to Read
1. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
2. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen3/PROJECT.md`
3. Current models, serializers, views, services in `moc-backend/chat/` and `moc-backend/orders/`.

## Specific Investigation Scope
1. **Chat Consumer & Persistence Flow**:
   - Model structure of `HoiThoai` (conversation) and `TinNhan` (message) in `chat/models.py`.
   - Consumer design (`AsyncWebsocketConsumer` or `JsonWebsocketConsumer`):
     * `connect()`: extract `conversation_id`, join channel group `chat_{conversation_id}`.
     * `receive_json()`: validate payload, check sender, save message to DB asynchronously (`database_sync_to_async(TinNhan.objects.create)`), then broadcast to group.
     * `disconnect()`: leave channel group.
     * `chat_message()`: handler sending message JSON to client.
   - REST API for chat history:
     * Endpoint `/api/chat/conversations/` or `/api/chat/hoi-thoai/` to retrieve messages and active sessions.
2. **Order FSM Lifecycle & Real-time Broadcast**:
   - Model structure of `DonHang` and `LichSuTrangThaiDon` in `orders/models.py`.
   - FSM service / method in `orders/services.py`:
     * Validation of transition (e.g. check current state against transition table).
     * Atomic transaction: update `trang_thai`, create `LichSuTrangThaiDon(don_hang=..., trang_thai_cu=..., trang_thai_moi=..., ghi_chu=...)`.
     * Trigger broadcast: using `get_channel_layer().group_send()` to send event `order_status_update` to `order_{ma_don_hang}` and `staff_orders`.
   - REST API endpoint:
     * Action `cap_nhat_trang_thai` or `chuyen_trang_thai` on `DonHangViewSet` for staff/admin to transition state with audit log.
   - Order WebSocket Consumer:
     * Client order tracking consumer `/ws/orders/<order_id>/` joining `order_{order_id}`.
     * Staff order consumer `/ws/orders/staff/` joining `staff_orders` for kitchen/waiter staff.
3. **Verification & Testing Strategy**:
   - Concrete test cases for:
     * Chat consumer: message echo, broadcast to multiple connections, DB persistence check.
     * Order FSM: valid transitions, invalid transition rejection (HTTP 400), audit log creation, broadcast event emitted.
     * Unauthenticated connection handling.

## Output Deliverable
Write your complete technical implementation design to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m3_2/handoff.md`
and notify caller when complete.


## 2026-10-14T10:28:49Z
[Message] sender=3b4ac039-b543-49a4-9b3d-21e996771d3e priority=MESSAGE_PRIORITY_HIGH
You are m3_explorer_2, the Chat & Order FSM Implementation Explorer for Milestone 3.
Your working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m3_2
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m3_2/DISPATCH.md
MANDATORY: Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen3/PROJECT.md before starting work.
Investigate and design technical implementation for:
1. ChatConsumer in moc-backend/chat/consumers.py: connect, receive_json, disconnect, asynchronous DB persistence into TinNhan model before group broadcast, and chat history REST API.
2. Order FSM Service & Consumers in moc-backend/orders/: 6-state transition validation, LichSuTrangThaiDon audit logging, channel_layer group_send broadcast, OrderConsumer for tracking and staff.
3. Verification test suite plan for chat persistence, broadcast echo, and FSM transition rules.
Write your complete implementation design report to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m3_2/handoff.md and notify the caller when done.


## 2026-10-14T15:09:05Z
[User Message] tiếp tục các công việc đang ngưng
