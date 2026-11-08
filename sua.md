3.  chat/consumers.py
    a) Thêm import: from .services import STAFF*GROUP, is_staff_user, save_message
    b) Đầu receive_json, thêm keep-alive:
    python
    if content.get("action") == "ping":
    await self.send_json({"type": "pong"})
    return
    c) Trong nhánh send_message, thay khối msg_payload = await self.\_save_message(...) và broadcast_event (đang có "data": msg_payload, **msg_payload) bằng:
    python
    room, msg_payload = await self.\_save_message(
    room_id=self.room.id, user=self.user, text=text,
    msg_type=msg_type, client_id=content.get("client_id"),
    )
    await self.channel_layer.group_send(self.room_group_name, {"type": "chat_message", **msg_payload})
    inbox = {"type": "inbox_update", "conversation_id": room.id,
    "customer_id": room.khach_hang_id, "last_message": msg_payload}
    await self.channel_layer.group_send(STAFF_GROUP, inbox)
    await self.channel_layer.group_send(f"user*{room.khach*hang_id}", inbox)
    d) Thay toàn bộ hàm \_save_message (cả dict payload dài 20 key) bằng:
    python
    @database_sync_to_async
    def \_save_message(self, **kwargs):
    return save_message(**kwargs)
    e) Thêm vào cuối file:
    python
    class InboxConsumer(AsyncJsonWebsocketConsumer):
    """Staff: nhận mọi tin mới. Khách: nhận tin thuộc room của mình."""
    async def connect(self):
    user = self.scope.get("user")
    if not user or not user.is_authenticated:
    await self.close(code=4401)
    return
    self.group = STAFF_GROUP if is_staff_user(user) else f"user*{user.id}"
    await self.channel_layer.group_add(self.group, self.channel_name)
    await self.accept()

        async def disconnect(self, code):
            if hasattr(self, "group"):
                await self.channel_layer.group_discard(self.group, self.channel_name)

        async def inbox_update(self, event):
            await self.send_json(event)

        async def receive_json(self, content, **kwargs):
            if content.get("action") == "ping":
                await self.send_json({"type": "pong"})

4.  chat/routing.py
    Hiện regex [a-zA-Z0-9_-]+ sẽ bắt luôn chữ inbox. Thay toàn bộ:
    python
    websocket_urlpatterns = [
    re_path(r"^ws/chat/inbox/?$", consumers.InboxConsumer.as_asgi()),
    re_path(r"^ws/chat/(?P<conversation_id>\d+)/?$", consumers.ChatConsumer.as_asgi()),
    re_path(r"^ws/hoi-thoai/(?P<conversation_id>\d+)/?$", consumers.ChatConsumer.as_asgi()),
    ]
5.  chat/views.py (HoiThoaiViewSet; giữ nguyên get_permissions, active, perform_create)
    Thêm import from django.db.models import Count, F, OuterRef, Q, Subquery, from .services import broadcast_message, broadcast_read, save_message, serialize_message, is_staff_user, và HoiThoaiListSerializer từ .serializers.
    python
    def get_serializer_class(self):
    return HoiThoaiListSerializer if self.action == "list" else HoiThoaiSerializer

def get_queryset(self):
q = HoiThoai.objects.select_related("khach_hang")
user = self.request.user
if not is_staff_user(user):
return q.filter(khach_hang=user)
if self.action == "list":
last = TinNhan.objects.filter(hoi_thoai=OuterRef("pk")).order_by("-id")
q = q.annotate(
unread_count=Count("danh_sach_tin_nhan", filter=Q(
danh_sach_tin_nhan**da_doc=False,
danh_sach_tin_nhan**nguoi_gui_id=F("khach_hang_id"))),
last_message=Subquery(last.values("noi_dung")[:1]),
).order_by(F("tin_nhan_cuoi_luc").desc(nulls_last=True))
return q

@action(detail=True, methods=["get", "post"])
def messages(self, request, pk=None):
room = self.get_object()
if request.method == "POST":
ser = TinNhanSerializer(data=request.data)
ser.is_valid(raise_exception=True)
data = ser.validated_data
text = (data.get("noi_dung") or "").strip()
if not text:
return Response({"noi_dung": ["Nội dung trống."]}, status=400)
room, payload = save_message(
room_id=room.id, user=request.user, text=text[:5000],
msg_type=data.get("loai_tin_nhan") or "van_ban",
client_id=request.data.get("client_id"))
broadcast_message(room, payload) # trước đây thiếu dòng này
return Response(payload, status=201)

    qs = room.danh_sach_tin_nhan.select_related("nguoi_gui")
    if request.query_params.get("after_id"):       # bù tin sau reconnect
        qs = qs.filter(id__gt=request.query_params["after_id"]).order_by("id")[:200]
        return Response([serialize_message(m) for m in qs])
    if request.query_params.get("before_id"):
        qs = qs.filter(id__lt=request.query_params["before_id"])
    items = list(qs.order_by("-id")[:50])[::-1]    # 50 tin gần nhất
    return Response([serialize_message(m) for m in items])

@action(detail=True, methods=["post"], url_path="mark_read")
def mark_read(self, request, pk=None):
room = self.get_object()
room.danh_sach_tin_nhan.filter(da_doc=False).exclude(nguoi_gui=request.user)\
 .update(da_doc=True, doc_luc=timezone.now())
broadcast_read(room, request.user)
return Response({"ok": True})
gui_tin_nhan có thể xóa, hoặc giữ làm wrapper gọi self.messages(request, pk=pk). 6. chat/serializers.py
Trong HoiThoaiSerializer, xóa hai field danh_sach_tin_nhan và messages (đang làm mỗi lần gọi trả tin nhắn hai lần).
Thêm:
python
class HoiThoaiListSerializer(serializers.ModelSerializer):
customer_name = serializers.SerializerMethodField()
last_message = serializers.CharField(read_only=True, default="")
unread_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = HoiThoai
        fields = ("id", "customer_name", "trang_thai", "tin_nhan_cuoi_luc",
                  "last_message", "unread_count")

    def get_customer_name(self, obj):
        return obj.khach_hang.get_full_name() or obj.khach_hang.username

Kiểm tra api/urls.py: admin đang gọi /chat/rooms/, còn hook của khách gọi /chat/conversations/. Bạn nên chỉ để một prefix, hoặc chắc chắn cả hai cùng trỏ tới HoiThoaiViewSet.
Frontend 7. src/hooks/useWebSocketChat.ts
Xóa effect có setInterval(... syncMessages ..., 3000).
Trong connect() dùng new WebSocket(getWebSocketUrl(...)) thay vì wsUrl tính một lần ở đầu effect (token hết hạn thì reconnect vẫn dùng token cũ).
Trong formatMessage: const isMe = myId !== null && senderId === myId; (bỏ && !raw.is_staff).
Thêm open?: boolean vào options, dùng openRef: mergeMessages([msg], !openRef.current), và gửi mark_read khi open đổi thành true hoặc ngay sau onopen.
Trong chat_read_receipt: bỏ qua nếu data.reader_id === user.id, và chỉ đánh dấu tin from === "me" có id ≤ last_read_message_id.
Thêm backoff và ping:
ts
ws.onopen = () => { retry = 0; setIsConnected(true); void syncMessages(conversationId);
pingTimer = setInterval(() => ws.readyState === WebSocket.OPEN &&
ws.send(JSON.stringify({ action: "ping" })), 25000); };
ws.onclose = (e) => { clearInterval(pingTimer); setIsConnected(false);
if (!isClosing && e.code !== 4401 && e.code !== 4403)
reconnectTimeoutRef.current = setTimeout(connect, Math.min(1000 \* 2 \*\* retry++, 15000)); };
Nhánh fallback REST trong sendMessage: bây giờ server đã broadcast nên vẫn an toàn. 8. src/hooks/useChatInbox.ts (file mới)
Dùng lại hook ở tin trước (kết nối /ws/chat/inbox/, tải /chat/conversations/ hoặc /chat/rooms/ một lần khi connect/reconnect, cập nhật unread qua inbox_update). Thêm tham số thứ ba onIncoming?: (item, message) => void, gọi nó khi nhận tin từ khách, để dùng cho toast. 9. src/admin/pages/ChatPage.tsx (file cần viết lại)
Bỏ chatStore.list() và sendChatMessage(), thay phần dữ liệu bằng:
tsx
const [activeId, setActiveId] = useState<number | null>(null);
const { items, loading, markSeen } = useChatInbox(true, activeId);
const { messages, isConnected, isTyping, sendMessage, sendTyping } = useWebSocketChat({
conversationId: activeId ?? undefined, enabled: activeId !== null, open: true,
});
Giữ JSX và Tailwind hiện có, chỉ đổi nguồn dữ liệu: danh sách dùng items (customerName, lastMessage, unread), tin nhắn dùng messages (m.from === "me" là tin của staff). Nút gửi gọi sendMessage(text), onChange gọi sendTyping. Khi chọn hội thoại thì gọi markSeen(id). 10. src/admin/layout/AdminLayout.tsx
Xóa effect polling (dòng setInterval(() => void poll(), 3000) và hàm poll gọi chatStore.list()). Thay bằng useChatInbox(true, null, (item, msg) => toast(...)), và tính badge Chat bằng tổng unread của items. 11. src/admin/api/admin.api.ts
Sau khi ChatPage và AdminLayout không còn dùng, xóa chatStore và sendChatMessage. Kiểm tra src/api/admin.api.ts nếu đây là bản trùng. 12. src/pages/admin/AdminChatPage.tsx
Không được route nào dùng. Sau khi ChatPage mới chạy ổn thì xóa file này để tránh hai bản chat lệch nhau. 13. src/components/chat/ChatWidget.tsx
Hiện enabled: open && isAuthenticated nên WS đóng khi widget đóng và unreadCount không bao giờ tăng. Sửa:
tsx
const [everOpened, setEverOpened] = useState(false);
const handleOpen = () => { setOpen(true); setEverOpened(true); };
const {...} = useWebSocketChat({ enabled: isAuthenticated && everOpened, open });
Bỏ clearUnread khỏi destructure (hook tự xử lý khi open đổi) và gọi handleOpen thay cho setOpen(true). Không bật enabled ngay khi đăng nhập, vì GET /active/ sẽ tạo HoiThoai cho mọi user. 14. src/services/websocket.ts và vite.config.ts (không bắt buộc)
Trên localhost mọi thứ vẫn chạy. Nếu bạn mở bằng IP LAN (Vite đang host: true), thêm proxy "/ws": { target: "ws://127.0.0.1:8000", ws: true } và cho getWebSocketUrl dùng window.location.host khi không có VITE_WS_URL. Đồng thời cho IP đó vào ALLOWED_HOSTS, vì AllowedHostsOriginValidator sẽ chặn.
