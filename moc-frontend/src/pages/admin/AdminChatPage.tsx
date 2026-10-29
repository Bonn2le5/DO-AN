import { useEffect, useState, useRef } from "react";
import { MessageCircle, Send, RefreshCw, Sparkles, User } from "lucide-react";
import {
  getAdminChatRooms,
  getAdminChatMessages,
  sendAdminChatMessage,
  updateChatRoomStatus,
  type AdminChatRoomItem,
  type AdminChatMessageItem,
} from "@/api/admin.api";
import { useAuthStore } from "@/store/authStore";
import { getWebSocketUrl } from "@/services/websocket";

const CANNED_RESPONSES = [
  "Dạ Mộc Quán xin chào quý khách! Em có thể giúp gì cho mình ạ? 👋",
  "Bàn của quý khách đã được chuẩn bị sẵn sàng, mời quý khách đến nhận bàn ạ.",
  "Đơn hàng của quý khách đang được bếp chế biến, dự kiến khoảng 15-20 phút nữa sẽ giao tới ạ.",
  "Dạ vâng, em đã ghi nhận thông tin và cập nhật giúp mình rồi ạ.",
];

export default function AdminChatPage() {
  const { user } = useAuthStore();
  const [rooms, setRooms] = useState<AdminChatRoomItem[]>([]);
  const [activeRoom, setActiveRoom] = useState<AdminChatRoomItem | null>(null);
  const [messages, setMessages] = useState<AdminChatMessageItem[]>([]);
  const [draft, setDraft] = useState("");
  const [customerTyping, setCustomerTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchRooms = async () => {
    try {
      const data = await getAdminChatRooms();
      setRooms(data);
      if (!activeRoom && data.length > 0) {
        selectRoom(data[0]);
      }
    } catch (err) {
      console.error("Failed to load chat rooms:", err);
    } finally {
      setLoading(false);
    }
  };

  const selectRoom = async (room: AdminChatRoomItem) => {
    setActiveRoom(room);
    try {
      const msgs = await getAdminChatMessages(room.id);
      setMessages(msgs);
      setTimeout(scrollToBottom, 100);
    } catch (err) {
      console.error("Failed to load messages:", err);
    }
  };

  useEffect(() => {
    fetchRooms();
  }, []);

  // WebSocket Connection per Active Room
  useEffect(() => {
    if (!activeRoom) return;

    const wsUrl = getWebSocketUrl(`/ws/chat/${activeRoom.id}/`);

    let ws: WebSocket;
    try {
      ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);

          if (payload.type === "chat_message") {
            const newMsg: AdminChatMessageItem = {
              id: payload.id || Date.now(),
              hoi_thoai: activeRoom.id,
              nguoi_gui: payload.sender_id,
              sender_name: payload.sender_name,
              noi_dung: payload.content || payload.noi_dung || payload.message,
              loai_tin_nhan: payload.message_type || "van_ban",
              da_doc: payload.is_read ?? false,
              tao_luc: payload.created_at || new Date().toISOString(),
              is_staff: payload.is_staff,
            };

            setMessages((prev) => {
              if (prev.some((m) => m.id === newMsg.id)) return prev;
              return [...prev, newMsg];
            });
            setTimeout(scrollToBottom, 50);
          } else if (payload.type === "chat_typing") {
            if (!payload.is_staff) {
              setCustomerTyping(Boolean(payload.is_typing));
              if (payload.is_typing) {
                setTimeout(() => setCustomerTyping(false), 3000);
              }
            }
          }
        } catch (e) {
          console.error("WS Parse Error", e);
        }
      };

      ws.onclose = () => setIsConnected(false);
      ws.onerror = () => setIsConnected(false);
    } catch (err) {
      setIsConnected(false);
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [activeRoom?.id]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || draft).trim();
    if (!text || !activeRoom) return;

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          action: "send_message",
          message: text,
          content: text,
          noi_dung: text,
        })
      );
    } else {
      // REST fallback
      try {
        const sent = await sendAdminChatMessage(activeRoom.id, text);
        setMessages((prev) => [...prev, sent]);
      } catch (err) {
        alert("Không thể gửi tin nhắn.");
      }
    }

    setDraft("");
    setTimeout(scrollToBottom, 50);
  };

  const handleToggleRoomStatus = async () => {
    if (!activeRoom) return;
    const newStatus = activeRoom.trang_thai === "mo" ? "dong" : "mo";
    try {
      await updateChatRoomStatus(activeRoom.id, newStatus);
      setActiveRoom({ ...activeRoom, trang_thai: newStatus });
      fetchRooms();
    } catch (err) {
      alert("Không thể cập nhật trạng thái hội thoại.");
    }
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col bg-white border rounded-xl shadow-sm overflow-hidden">
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Rooms List */}
        <div className="w-80 border-r flex flex-col bg-gray-50/50">
          <div className="p-4 border-b flex justify-between items-center bg-white">
            <h2 className="font-bold text-gray-900 flex items-center gap-2">
              <MessageCircle className="w-5 h-5 text-primary" /> Hội thoại khách hàng
            </h2>
            <button onClick={fetchRooms} className="text-gray-400 hover:text-gray-600" title="Tải lại">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-gray-100">
            {loading ? (
              <div className="p-6 text-center text-sm text-gray-500">Đang tải...</div>
            ) : rooms.length === 0 ? (
              <div className="p-6 text-center text-sm text-gray-400">Chưa có hội thoại nào</div>
            ) : (
              rooms.map((room) => {
                const isSelected = activeRoom?.id === room.id;
                const lastMsg = room.danh_sach_tin_nhan?.[room.danh_sach_tin_nhan.length - 1];
                return (
                  <button
                    key={room.id}
                    onClick={() => selectRoom(room)}
                    className={`w-full text-left p-4 transition-colors flex items-start gap-3 ${
                      isSelected ? "bg-white border-l-4 border-primary shadow-xs" : "hover:bg-gray-100/60"
                    }`}
                  >
                    <div className="w-10 h-10 rounded-full bg-primary/10 text-primary font-bold flex items-center justify-center shrink-0">
                      <User className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-baseline">
                        <span className="font-semibold text-sm text-gray-900 truncate">
                          Khách #{room.khach_hang}
                        </span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${room.trang_thai === "mo" ? "bg-green-100 text-green-700" : "bg-gray-200 text-gray-600"}`}>
                          {room.trang_thai === "mo" ? "Đang mở" : "Đã đóng"}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 truncate mt-1">
                        {lastMsg?.noi_dung || "Chưa có tin nhắn"}
                      </p>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right: Live Chat Pane */}
        {activeRoom ? (
          <div className="flex-1 flex flex-col bg-white">
            {/* Header */}
            <div className="p-4 border-b flex justify-between items-center bg-gray-50/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold">
                  K{activeRoom.khach_hang}
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 text-sm">Khách hàng #{activeRoom.khach_hang}</h3>
                  <div className="flex items-center gap-1.5 text-xs">
                    <span className={`w-2 h-2 rounded-full ${isConnected ? "bg-emerald-500" : "bg-amber-400"}`} />
                    <span className="text-gray-500">{isConnected ? "Đã kết nối thời gian thực" : "Mất kết nối WS"}</span>
                  </div>
                </div>
              </div>

              <button
                onClick={handleToggleRoomStatus}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                  activeRoom.trang_thai === "mo"
                    ? "bg-red-50 text-red-600 border-red-200 hover:bg-red-100"
                    : "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100"
                }`}
              >
                {activeRoom.trang_thai === "mo" ? "Đóng hội thoại" : "Mở lại hội thoại"}
              </button>
            </div>

            {/* Messages Body */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50/30">
              {messages.map((m) => {
                const isStaff = m.is_staff || m.nguoi_gui === Number(user?.id);
                return (
                  <div key={m.id} className={`flex flex-col ${isStaff ? "items-end" : "items-start"}`}>
                    <div className="text-[11px] text-gray-400 mb-1 px-1">
                      {isStaff ? "Nhân viên hỗ trợ" : `Khách #${m.nguoi_gui}`}
                    </div>
                    <div
                      className={`max-w-md px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                        isStaff
                          ? "bg-primary text-white rounded-br-xs"
                          : "bg-white border text-gray-800 rounded-bl-xs shadow-xs"
                      }`}
                    >
                      {m.noi_dung}
                    </div>
                    <div className="text-[10px] text-gray-400 mt-1 px-1">
                      {new Date(m.tao_luc).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </div>
                  </div>
                );
              })}
              {customerTyping && (
                <div className="text-xs text-gray-400 italic flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" />
                  Khách hàng đang nhập tin nhắn...
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Quick Canned Responses */}
            <div className="px-4 py-2 border-t bg-gray-50 flex gap-2 overflow-x-auto">
              <span className="text-xs font-semibold text-gray-400 flex items-center gap-1 shrink-0">
                <Sparkles className="w-3.5 h-3.5 text-amber-500" /> Tin mẫu:
              </span>
              {CANNED_RESPONSES.map((res, i) => (
                <button
                  key={i}
                  onClick={() => handleSendMessage(res)}
                  className="px-2.5 py-1 bg-white border rounded-full text-xs text-gray-600 hover:border-primary hover:text-primary shrink-0 transition-colors"
                >
                  {res.slice(0, 32)}...
                </button>
              ))}
            </div>

            {/* Input Bar */}
            <div className="p-3 border-t bg-white flex gap-2">
              <input
                type="text"
                placeholder="Nhập nội dung phản hồi khách hàng..."
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
                className="flex-1 px-4 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <button
                onClick={() => handleSendMessage()}
                className="px-5 py-2.5 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90 flex items-center gap-1.5"
              >
                <Send className="w-4 h-4" /> Gửi
              </button>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
            Chọn một cuộc hội thoại từ danh sách bên trái để bắt đầu chat
          </div>
        )}
      </div>
    </div>
  );
}
