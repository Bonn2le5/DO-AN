import { useEffect, useRef, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { ArrowLeft, Send } from "lucide-react";
import { apiClient } from "@/api/client";
import { useWebSocketChat } from "@/hooks/useWebSocketChat";
import type { ChatInbox } from "@/hooks/useChatInbox";
import { inputCls, StatusBadge } from "../components/primitives";
import { useToast } from "../components/toast";
import { useCan, useRole } from "../permissions";
import { useAsync } from "@/hooks/useAsync";
import { getTableManagementBranches } from "../api/admin.api";
import { fmtDateTime } from "../lib";
import { cn } from "@/lib/utils";
import MessageMeta from "@/components/chat/MessageMeta";

/** Nhãn vai trò cho tin của người khác bên nhà hàng. */
const ROLE_LABEL: Record<string, string> = { admin: "Admin tổng", quan_ly: "Quản lý chi nhánh", nhan_vien: "Nhân viên" };

export default function ChatPage() {
  const can = useCan();
  const isAdmin = useRole() === "admin";
  const push = useToast((s) => s.push);
  const { items, loading, setActive, setStatus, reload } =
    useOutletContext<ChatInbox>();
  // Admin giao hội thoại cho chi nhánh; nhân viên/quản lý chỉ thấy hội thoại của chi nhánh mình.
  const { data: branches } = useAsync(() => (isAdmin ? getTableManagementBranches() : Promise.resolve([])), [isAdmin]);
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

  const transfer = async (branchId: string) => {
    if (!active) return;
    try {
      await apiClient.post(`/hoi-thoai/${active.id}/chuyen-chi-nhanh/`, { chi_nhanh: branchId || null });
      const name = branches?.find((b) => b.id === branchId)?.name;
      push(name ? `Đã chuyển hội thoại cho ${name}` : "Hội thoại chuyển về hộp thư chung");
      await reload();
    } catch {
      push("Không chuyển được hội thoại", "err");
    }
  };

  const close = async () => {
    if (!active) return;
    try {
      await apiClient.patch(`/hoi-thoai/${active.id}/`, {
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
        <div className="px-5 py-4 border-b border-black/[0.07]">
          <div className="font-display text-lg">Hội thoại</div>
          {!isAdmin && <div className="text-xs text-muted mt-0.5">Khách liên hệ chi nhánh của bạn</div>}
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
              {isAdmin && (
                <div className={cn("text-[11px] mt-0.5 truncate", c.branchId ? "text-muted" : "text-primary font-medium")}>
                  {c.branchId ? c.branchName.replace(/^Nhà hàng Mộc\s*-\s*/i, "") : "Chưa giao chi nhánh"}
                </div>
              )}
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
              {isAdmin && (
                <label className="hidden sm:block">
                  <span className="sr-only">Chi nhánh phụ trách</span>
                  <select value={active.branchId ?? ""} onChange={(e) => void transfer(e.target.value)} className="h-9 max-w-52 rounded-lg border border-black/10 bg-white px-2 text-[13px]" title="Chi nhánh phụ trách trả lời">
                    <option value="">Hộp thư chung (admin)</option>
                    {(branches ?? []).map((b) => <option key={b.id} value={b.id}>{b.name.replace(/^Nhà hàng Mộc\s*-\s*/i, "")}</option>)}
                  </select>
                </label>
              )}
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
              {messages.map((m) => {
                // Ba loại tin: của mình, của người khác bên nhà hàng (admin/quản lý/nhân viên), của khách.
                // Tin nhà hàng luôn nằm bên phải để không bị nhầm là khách tự nói.
                const mine = m.from === "me";
                const teammate = !mine && m.isStaff;
                return (
                  <div key={m.id} className={cn("flex flex-col", mine || teammate ? "items-end" : "items-start")}>
                    {teammate && (
                      <span className="mb-1 mr-1 text-[11px] text-muted">
                        {m.senderName}
                        {ROLE_LABEL[m.senderRole ?? ""] && <span className="ml-1.5 rounded bg-dark/80 px-1.5 py-0.5 font-medium text-white">{ROLE_LABEL[m.senderRole ?? ""]}</span>}
                      </span>
                    )}
                    <div
                      className={cn(
                        "max-w-[78%] rounded-2xl px-3.5 py-2.5 text-sm",
                        mine && "bg-primary text-white rounded-br-sm",
                        teammate && "bg-dark text-white rounded-br-sm",
                        !mine && !teammate && "bg-white border border-black/[0.07] rounded-bl-sm",
                      )}
                    >
                      {m.content}
                      <MessageMeta time={fmtDateTime(m.createdAt)} mine={mine} isRead={m.isRead} className={mine || teammate ? "text-white/70" : "text-muted justify-start"} />
                    </div>
                  </div>
                );
              })}
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
