/**
 * Production-ready Real-time Customer Support Chat Widget.
 * Connects to Django Channels WebSocket at /ws/chat/<conversation_id>/?token=<access_token>.
 * Path: moc-frontend/src/components/chat/ChatWidget.tsx
 */

import { useState, useRef, useEffect } from "react";
import { MessageCircle, X, Send, LogIn } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { useWebSocketChat } from "@/hooks/useWebSocketChat";

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const draftRef = useRef("");
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  const {
    messages,
    isConnected,
    isTyping,
    typingUser,
    unreadCount,
    loadingHistory,
    sendMessage,
    sendTyping,
    clearUnread,
  } = useWebSocketChat({ enabled: open && isAuthenticated });

  // Scroll to bottom when messages update
  useEffect(() => {
    if (open) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, open, isTyping]);

  const handleOpen = () => {
    setOpen(true);
    clearUnread();
  };

  const handleSend = () => {
    const text = draftRef.current.trim();
    if (!text) return;
    draftRef.current = "";
    setDraft("");
    sendMessage(text);
    sendTyping(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    draftRef.current = e.target.value;
    setDraft(e.target.value);
    sendTyping(e.target.value.length > 0);
  };

  return (
    <div className="fixed bottom-6 right-6 z-[95] flex flex-col items-end gap-3">
      {open && (
        <div className="w-[320px] sm:w-[380px] h-[480px] bg-white rounded-2xl shadow-lift border border-black/[0.08] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
          {/* Header */}
          <div className="bg-dark text-white px-5 py-4 flex items-center justify-between">
            <div>
              <div className="font-display text-[15px] font-semibold">Nhà hàng MỘC</div>
              <div className="text-[11.5px] text-white/70 flex items-center gap-1.5 mt-0.5">
                <span
                  className={`w-2 h-2 rounded-full inline-block ${
                    isConnected ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
                  }`}
                />
                {isConnected ? "Trực tuyến (Real-time)" : "Đang kết nối..."}
              </div>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="text-white/70 hover:text-white transition-colors p-1"
            >
              <X width={18} height={18} />
            </button>
          </div>

          {/* Chat Body */}
          {!isAuthenticated ? (
            <div className="flex-1 flex flex-col items-center justify-center p-6 text-center bg-bg">
              <div className="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center mb-3">
                <LogIn width={22} height={22} />
              </div>
              <h4 className="font-display text-base mb-1">Đăng nhập để trò chuyện</h4>
              <p className="text-xs text-muted mb-4 max-w-[240px]">
                Vui lòng đăng nhập vào tài khoản để kết nối trực tiếp với nhân viên hỗ trợ nhà hàng.
              </p>
              <Link
                to="/dang-nhap"
                onClick={() => setOpen(false)}
                className="btn btn-primary text-xs py-2 px-4"
              >
                Đăng nhập ngay
              </Link>
            </div>
          ) : (
            <>
              <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 bg-bg">
                {loadingHistory && (
                  <div className="text-center text-xs text-muted py-2">
                    Đang tải lịch sử trò chuyện...
                  </div>
                )}

                {messages.length === 0 && !loadingHistory && (
                  <div className="text-center text-xs text-muted py-6">
                    Chưa có tin nhắn nào. Hãy gửi lời chào đến Mộc nhé! 👋
                  </div>
                )}

                {messages.map((m) => {
                  const isMe = m.from === "me";
                  return (
                    <div key={m.id} className={isMe ? "flex justify-end" : "flex justify-start"}>
                      <div
                        className={
                          isMe
                            ? "bg-primary text-white text-[13.5px] px-3.5 py-2.5 rounded-2xl rounded-br-sm max-w-[78%] shadow-sm"
                            : "bg-white border border-black/[0.07] text-text text-[13.5px] px-3.5 py-2.5 rounded-2xl rounded-bl-sm max-w-[78%] shadow-sm"
                        }
                      >
                        {!isMe && (
                          <div className="text-[10px] font-semibold text-primary mb-1">
                            {m.senderName} {m.isStaff && "• Nhân viên"}
                          </div>
                        )}
                        <div>{m.content}</div>
                        <div
                          className={
                            isMe
                              ? "text-[9.5px] text-white/70 mt-1 text-right"
                              : "text-[9.5px] text-muted mt-1"
                          }
                        >
                          {m.time} {isMe && (m.isRead ? "✓✓" : "✓")}
                        </div>
                      </div>
                    </div>
                  );
                })}

                {isTyping && (
                  <div className="flex items-center gap-1.5 text-xs text-muted italic px-2 py-1">
                    <span className="w-1.5 h-1.5 bg-primary/60 rounded-full animate-bounce" />
                    <span>{typingUser || "Nhân viên"} đang nhập...</span>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="flex items-center gap-2 border-t border-black/[0.07] p-3 bg-white">
                <input
                  value={draft}
                  onChange={handleInputChange}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      if (!e.repeat) handleSend();
                    }
                  }}
                  placeholder="Nhập tin nhắn..."
                  className="flex-1 min-w-0 px-3.5 py-2.5 rounded-full bg-bg text-sm outline-none focus:ring-1 focus:ring-primary/40"
                />
                <button
                  onClick={handleSend}
                  disabled={!draft.trim()}
                  className="w-9 h-9 rounded-full bg-primary disabled:opacity-40 text-white flex items-center justify-center flex-shrink-0 transition-opacity"
                >
                  <Send width={15} height={15} />
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {/* Floating Toggle Button */}
      <button
        onClick={open ? () => setOpen(false) : handleOpen}
        className="w-14 h-14 rounded-full bg-primary text-white shadow-lift flex items-center justify-center hover:scale-105 transition-transform relative"
        aria-label="Trò chuyện với nhà hàng"
      >
        {open ? <X width={22} height={22} /> : <MessageCircle width={22} height={22} />}
        {!open && unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-dark text-white text-[10px] font-bold flex items-center justify-center animate-bounce">
            {unreadCount}
          </span>
        )}
      </button>
    </div>
  );
}
