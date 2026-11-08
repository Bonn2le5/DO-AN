import { useEffect, useRef, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { ArrowLeft, Send } from "lucide-react";
import { apiClient } from "@/api/client";
import { useWebSocketChat } from "@/hooks/useWebSocketChat";
import type { ChatInbox } from "@/hooks/useChatInbox";
import { inputCls, StatusBadge } from "../components/primitives";
import { useToast } from "../components/toast";
import { useCan } from "../permissions";
import { fmtDateTime } from "../lib";
import { cn } from "@/lib/utils";

export default function ChatPage() {
  const can = useCan();
  const push = useToast((s) => s.push);
  const { items, loading, setActive, setStatus } =
    useOutletContext<ChatInbox>();
  const [activeId, setActiveId] = useState<number | null>(null);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);
  const active = items.find((c) => c.id === activeId);

  const {
    messages,
    isConnected,
    isTyping,
    typingUser,
    loadingHistory,
    sendMessage,
    sendTyping,
  } = useWebSocketChat({
    conversationId: activeId ?? undefined,
    enabled: activeId !== null,
    open: true,
  });

  // Báo cho inbox biết hội thoại nào đang mở (không đếm unread cho nó).
  useEffect(() => {
    setActive(activeId);
    return () => setActive(null);
  }, [activeId, setActive]);

  // Desktop: tự chọn hội thoại đầu tiên như trước.
  useEffect(() => {
    if (
      activeId === null &&
      items.length > 0 &&
      window.matchMedia("(min-width: 768px)").matches
    ) {
      setActiveId(items[0].id);
    }
  }, [items, activeId]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "end" });
  }, [messages.length, activeId, isTyping]);

  const send = async () => {
    const text = draft.trim();
    if (!active || !text || sending) return;
    setSending(true);
    setDraft("");
    sendTyping(false);
    const ok = await sendMessage(text);
    if (!ok) {
      setDraft(text);
      push("Không gửi được tin nhắn", "err");
    }
    setSending(false);
  };

  const close = async () => {
    if (!active) return;
    try {
      await apiClient.patch(`/chat/conversations/${active.id}/`, {
        trang_thai: "dong",
      });
      setStatus(active.id, "closed");
      push("Đã đóng hội thoại");
    } catch {
      push("Không đóng được hội thoại", "err");
    }
  };

  return (
    <div className="card overflow-hidden grid md:grid-cols-[320px_1fr] h-[calc(100vh-8rem)] min-h-120">
      <div
        className={cn(
          "border-r border-black/[0.07] overflow-y-auto",
          activeId && "hidden md:block",
        )}
      >
        <div className="px-5 py-4 border-b border-black/[0.07] font-display text-lg">
          Hội thoại
        </div>
        {loading ? (
          <div className="p-5 space-y-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-14 rounded-xl bg-black/5 animate-pulse"
              />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="p-5 text-sm text-muted">Chưa có hội thoại nào.</div>
        ) : (
          items.map((c) => (
            <button
              key={c.id}
              onClick={() => setActiveId(c.id)}
              className={cn(
                "w-full text-left px-5 py-3.5 border-b border-black/5 hover:bg-black/3",
                c.id === activeId && "bg-primary/6",
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-semibold">{c.customerName}</span>
                {c.unread > 0 && (
                  <span className="min-w-5 h-5 px-1.5 rounded-full bg-primary text-white text-[11px] font-bold flex items-center justify-center">
                    {c.unread}
                  </span>
                )}
              </div>
              <div className="text-[13px] text-muted line-clamp-1 mt-1">
                {c.lastMessage}
              </div>
              <div className="text-[11px] text-muted mt-0.5">
                {c.lastAt && fmtDateTime(c.lastAt)}
                {c.status === "closed" && " · đã đóng"}
              </div>
            </button>
          ))
        )}
      </div>

      <div
        className={cn("flex-col min-h-0", activeId ? "flex" : "hidden md:flex")}
      >
        {!active ? (
          <div className="m-auto text-center px-6">
            <div className="font-display text-lg mb-1">Chọn một hội thoại</div>
            <p className="text-sm text-muted">
              Tin nhắn của khách sẽ hiện ở đây.
            </p>
          </div>
        ) : (
          <>
            <div className="px-5 py-3.5 border-b border-black/[0.07] flex items-center gap-3">
              <button
                className="md:hidden icon-btn"
                onClick={() => setActiveId(null)}
                aria-label="Quay lại danh sách"
              >
                <ArrowLeft width={18} height={18} />
              </button>
              <div className="flex-1">
                <div className="font-semibold">{active.customerName}</div>
                <div className="text-xs text-muted">
                  {isConnected ? "Đã kết nối trực tiếp" : "Đang kết nối lại…"}
                </div>
              </div>
              {active.status === "closed" ? (
                <StatusBadge>Đã đóng</StatusBadge>
              ) : (
                can("chat", "update") && (
                  <button
                    className="btn btn-outline py-2! px-4! text-[13px]!"
                    onClick={close}
                  >
                    Đóng hội thoại
                  </button>
                )
              )}
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3 bg-bg">
              {loadingHistory && messages.length === 0 && (
                <div className="text-center text-xs text-muted">
                  Đang tải lịch sử…
                </div>
              )}
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={cn(
                    "flex",
                    m.from === "me" ? "justify-end" : "justify-start",
                  )}
                >
                  <div
                    className={cn(
                      "max-w-[78%] rounded-2xl px-3.5 py-2.5 text-sm",
                      m.from === "me"
                        ? "bg-primary text-white rounded-br-sm"
                        : "bg-white border border-black/[0.07] rounded-bl-sm",
                    )}
                  >
                    {m.content}
                    <div
                      className={cn(
                        "text-[10px] mt-1",
                        m.from === "me" ? "text-white/70" : "text-muted",
                      )}
                    >
                      {fmtDateTime(m.createdAt)}{" "}
                      {m.from === "me" && (m.isRead ? "✓✓" : "✓")}
                    </div>
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="text-xs text-muted italic">
                  {typingUser ?? active.customerName} đang nhập…
                </div>
              )}
              <div ref={bottom} />
            </div>
            {active.status === "open" && can("chat", "create") && (
              <div className="p-3 border-t border-black/[0.07] flex gap-2">
                <input
                  value={draft}
                  onChange={(e) => {
                    setDraft(e.target.value);
                    sendTyping(e.target.value.length > 0);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      if (!e.repeat) void send();
                    }
                  }}
                  placeholder="Nhập tin nhắn…"
                  aria-label="Nhập tin nhắn"
                  className={inputCls}
                />
                <button
                  className="btn btn-primary w-11 h-11 p-0! rounded-full! shrink-0"
                  onClick={() => void send()}
                  disabled={sending}
                  aria-label="Gửi"
                >
                  <Send width={16} height={16} />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
