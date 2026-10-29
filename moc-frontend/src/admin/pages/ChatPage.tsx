import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, Send } from "lucide-react";
import { chatStore, sendChatMessage } from "../api/admin.api";
import { inputCls, StatusBadge } from "../components/primitives";
import { useToast } from "../components/toast";
import { useCan } from "../permissions";
import { fmtDateTime } from "../lib";
import { cn } from "@/lib/utils";

export default function ChatPage() {
  const can = useCan();
  const push = useToast((s) => s.push);
  const [rooms, setRooms] = useState<Awaited<ReturnType<typeof chatStore.list>>>([]);
  const [loading, setLoading] = useState(true);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);
  const refreshInFlight = useRef(false);
  const sendInFlight = useRef(false);
  const active = rooms.find((c) => c.id === activeId);

  const refreshRooms = useCallback(async () => {
    if (refreshInFlight.current) return;
    refreshInFlight.current = true;
    try {
      const nextRooms = await chatStore.list();
      setRooms(nextRooms);
      setActiveId((current) => current ?? nextRooms[0]?.id ?? null);
    } catch (error) {
      console.error("Không thể làm mới danh sách hội thoại:", error);
    } finally {
      refreshInFlight.current = false;
      setLoading(false);
    }
  }, [push]);

  useEffect(() => {
    void refreshRooms();
    const timer = window.setInterval(() => void refreshRooms(), 3000);
    return () => window.clearInterval(timer);
  }, [refreshRooms]);

  useEffect(() => { bottom.current?.scrollIntoView({ block: "end" }); }, [active?.messages.length, activeId]);

  const open = async (id: string) => {
    setActiveId(id);
    await chatStore.update(id, { unread: 0 });
    await refreshRooms();
  };
  const send = async () => {
    const text = draft.trim();
    if (!active || !text || sendInFlight.current) return;
    sendInFlight.current = true;
    setSending(true);
    setDraft("");
    try { await sendChatMessage(active.id, text); await refreshRooms(); }
    catch { setDraft(text); push("Không gửi được tin nhắn", "err"); }
    finally { sendInFlight.current = false; setSending(false); }
  };
  const close = async () => { if (active) { await chatStore.update(active.id, { status: "closed" }); push("Đã đóng hội thoại"); await refreshRooms(); } };

  return (
    <div className="card overflow-hidden grid md:grid-cols-[320px_1fr] h-[calc(100vh-8rem)] min-h-120">
      <div className={cn("border-r border-black/[0.07] overflow-y-auto", activeId && "hidden md:block")}>
        <div className="px-5 py-4 border-b border-black/[0.07] font-display text-lg">Hội thoại</div>
        {loading ? <div className="p-5 space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-14 rounded-xl bg-black/5 animate-pulse" />)}</div> :
          rooms.map((c) => {
            const last = c.messages[c.messages.length - 1];
            return (
              <button key={c.id} onClick={() => open(c.id)} className={cn("w-full text-left px-5 py-3.5 border-b border-black/5 hover:bg-black/3", c.id === activeId && "bg-primary/6")}>
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold flex items-center gap-2"><span className={cn("w-2 h-2 rounded-full", c.online ? "bg-success" : "bg-black/20")} />{c.customer}</span>
                  {c.unread > 0 && <span className="min-w-5 h-5 px-1.5 rounded-full bg-primary text-white text-[11px] font-bold flex items-center justify-center">{c.unread}</span>}
                </div>
                <div className="text-[13px] text-muted line-clamp-1 mt-1">{last?.text}</div>
                <div className="text-[11px] text-muted mt-0.5">{last && fmtDateTime(last.at)}{c.status === "closed" && " · đã đóng"}</div>
              </button>
            );
          })}
      </div>

      <div className={cn("flex-col min-h-0", activeId ? "flex" : "hidden md:flex")}>
        {!active ? (
          <div className="m-auto text-center px-6"><div className="font-display text-lg mb-1">Chọn một hội thoại</div><p className="text-sm text-muted">Tin nhắn của khách sẽ hiện ở đây.</p></div>
        ) : (
          <>
            <div className="px-5 py-3.5 border-b border-black/[0.07] flex items-center gap-3">
              <button className="md:hidden icon-btn" onClick={() => setActiveId(null)} aria-label="Quay lại danh sách"><ArrowLeft width={18} height={18} /></button>
              <div className="flex-1"><div className="font-semibold">{active.customer}</div><div className="text-xs text-muted">{active.online ? "Đang online" : "Offline"}</div></div>
              {active.status === "closed" ? <StatusBadge>Đã đóng</StatusBadge> : can("chat", "update") && <button className="btn btn-outline py-2! px-4! text-[13px]!" onClick={close}>Đóng hội thoại</button>}
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3 bg-bg">
              {active.messages.map((m) => (
                <div key={m.id} className={cn("flex", m.from === "staff" ? "justify-end" : "justify-start")}>
                  <div className={cn("max-w-[78%] rounded-2xl px-3.5 py-2.5 text-sm", m.from === "staff" ? "bg-primary text-white rounded-br-sm" : "bg-white border border-black/[0.07] rounded-bl-sm")}>
                    {m.text}<div className={cn("text-[10px] mt-1", m.from === "staff" ? "text-white/70" : "text-muted")}>{fmtDateTime(m.at)}</div>
                  </div>
                </div>
              ))}
              <div ref={bottom} />
            </div>
            {active.status === "open" && can("chat", "create") && (
              <div className="p-3 border-t border-black/[0.07] flex gap-2">
                <input value={draft} onChange={(e) => setDraft(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); if (!e.repeat) void send(); } }} placeholder="Nhập tin nhắn…" aria-label="Nhập tin nhắn" className={inputCls} />
                <button className="btn btn-primary w-11 h-11 p-0! rounded-full! shrink-0" onClick={() => void send()} disabled={sending} aria-label="Gửi"><Send width={16} height={16} /></button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
