import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, Check, ChefHat, Minus, NotebookPen, Plus, Printer, Search, X } from "lucide-react";
import { useToast } from "./toast";
import { inputCls } from "./primitives";
import { useAsync } from "@/hooks/useAsync";
import { formatCurrency } from "@/lib/utils";
import ConfirmModal from "./ConfirmModal";
import {
  cancelDiningSession,
  checkoutDiningSession,
  confirmDiningSessionCleaned,
  foodsStore,
  getDiningSession,
  getStockAlerts,
  moveDiningSession,
  ordersStore,
  replaceDiningSessionItems,
  setOrderStatus,
  lowStockMessage,
} from "../api/admin.api";
import { useCan, useRole } from "../permissions";
import { ORDER_META, ORDER_NEXT } from "../statusMeta";
import type { AdminFood } from "../data/mockCatalog";
import type { AdminDiningSession, AdminOrder, AdminTable } from "../types";

type CartLine = { foodId: string; name: string; category: string; price: number; image?: string; qty: number; note: string };
type Screen = "menu" | "invoice";
type PrintJob = { mode: "kot" | "bill"; lines: CartLine[] } | null;

interface Props {
  session: AdminDiningSession | null;
  tables: AdminTable[];
  onClose: () => void;
  onChanged: () => void;
}

const ALL = "Tất cả";
const lineKey = (line: Pick<CartLine, "foodId" | "note">) => `${line.foodId}|${line.note.trim()}`;
const sameCart = (a: CartLine[], b: CartLine[]) => JSON.stringify(a.map((l) => [lineKey(l), l.qty])) === JSON.stringify(b.map((l) => [lineKey(l), l.qty]));

function linesFromOrder(order: AdminOrder, foods: AdminFood[]): CartLine[] {
  const foodById = new Map(foods.map((food) => [food.id, food]));
  return order.items.map((item) => {
    const food = item.foodId ? foodById.get(item.foodId) : undefined;
    return { foodId: item.foodId ?? "", name: item.name, category: food?.category ?? "", price: item.price, image: item.image ?? food?.image, qty: item.qty, note: item.note ?? "" };
  });
}

function minutesSince(iso: string | undefined) {
  const t = iso ? new Date(iso).getTime() : NaN;
  if (Number.isNaN(t)) return null;
  const m = Math.max(0, Math.floor((Date.now() - t) / 60000));
  return m < 60 ? `${m} phút` : m < 1440 ? `${Math.floor(m / 60)} giờ ${m % 60} phút` : `${Math.floor(m / 1440)} ngày`;
}

export default function DiningSessionDrawer({ session, tables, onClose, onChanged }: Props) {
  const can = useCan();
  const role = useRole();
  const isManager = role === "admin" || role === "branch_manager";
  const [cancelOpen, setCancelOpen] = useState(false);
  const [releaseOpen, setReleaseOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState("");
  const push = useToast((state) => state.push);
  const searchRef = useRef<HTMLInputElement>(null);
  const [screen, setScreen] = useState<Screen>("menu");
  const [category, setCategory] = useState(ALL);
  const [search, setSearch] = useState("");
  const [cart, setCart] = useState<CartLine[]>([]);
  const [saved, setSaved] = useState<CartLine[]>([]);
  const [noteOpen, setNoteOpen] = useState<string | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<"cod" | "bank">("cod");
  const [paymentReference, setPaymentReference] = useState("");
  const [tendered, setTendered] = useState(0);
  const [busy, setBusy] = useState(false);
  const [printJob, setPrintJob] = useState<PrintJob>(null);
  const [guardOpen, setGuardOpen] = useState(false);
  const [ticketOpen, setTicketOpen] = useState(false); // chỉ dùng trên màn hẹp
  const [, setTick] = useState(0);

  const { data, loading, refetch } = useAsync(async () => {
    if (!session) return undefined;
    const [orders, foods, current, alerts] = await Promise.all([ordersStore.list(), foodsStore.list(), getDiningSession(session.id), getStockAlerts().catch(() => [])]);
    return { orders, foods, current, alerts };
  }, [session?.id]);

  const current = data?.current ?? session;
  const order = data?.orders.find((item) => item.id === current?.orderId);
  const foods = useMemo(() => data?.foods.filter((item) => item.available) ?? [], [data?.foods]);
  // Món có nguyên liệu dưới mức tối thiểu: đánh dấu để nhân viên báo khách trước khi gọi.
  const shortFoods = useMemo(() => {
    const map = new Map<string, string[]>();
    for (const a of data?.alerts ?? []) for (const name of a.foods) map.set(name, [...(map.get(name) ?? []), a.stock <= 0 ? `${a.name} đã hết` : `${a.name} còn ${a.stock}${a.unit ? " " + a.unit : ""}`]);
    return map;
  }, [data?.alerts]);
  const categories = useMemo(() => [ALL, ...new Set(foods.map((food) => food.category).filter(Boolean))], [foods]);
  const visibleFoods = useMemo(() => {
    const q = search.trim().toLowerCase();
    return foods.filter((food) => (category === ALL || food.category === category) && (!q || `${food.name} ${food.category}`.toLowerCase().includes(q)));
  }, [foods, category, search]);

  const canOperate = can("orders", "update");
  const orderClosed = !!order && (order.status === "cancelled" || order.status === "completed");
  const editable = canOperate && current?.status === "active" && !orderClosed;
  const sentToKitchen = !!order && order.status !== "pending";
  const dirty = !sameCart(cart, saved);

  // Món "mới" = phần số lượng chưa có trong lần gửi bếp trước.
  const savedQty = useMemo(() => {
    const map = new Map<string, number>();
    for (const line of saved) map.set(lineKey(line), (map.get(lineKey(line)) ?? 0) + line.qty);
    return map;
  }, [saved]);
  const newQtyOf = useCallback((line: CartLine) => (sentToKitchen ? Math.max(0, line.qty - (savedQty.get(lineKey(line)) ?? 0)) : line.qty), [sentToKitchen, savedQty]);
  const newLines = cart.map((line) => ({ ...line, qty: newQtyOf(line) })).filter((line) => line.qty > 0);
  const newCount = newLines.reduce((n, l) => n + l.qty, 0);
  const reducedSent = sentToKitchen && saved.some((line) => {
    const inCart = cart.filter((c) => lineKey(c) === lineKey(line)).reduce((n, c) => n + c.qty, 0);
    return inCart < line.qty;
  });
  const qtyByFood = useMemo(() => {
    const map = new Map<string, number>();
    for (const line of cart) map.set(line.foodId, (map.get(line.foodId) ?? 0) + line.qty);
    return map;
  }, [cart]);

  const subtotal = cart.reduce((sum, line) => sum + line.price * line.qty, 0);
  const discount = order?.discount ?? 0;
  const total = Math.max(0, subtotal - discount);
  const deposit = Math.min(current?.depositPaid ?? 0, total);
  const due = total - deposit;
  const itemCount = cart.reduce((n, l) => n + l.qty, 0);
  const destinationTables = useMemo(() => tables.filter((table) => (
    current && table.id !== current.tableId && table.branchId === current.branchId
    && table.status === "available" && !table.activeSession && table.capacity >= current.guestCount
  )), [current, tables]);
  const nextOrder = order && ORDER_NEXT[order.status];

  useEffect(() => {
    setScreen("menu"); setCategory(ALL); setSearch(""); setCart([]); setSaved([]); setNoteOpen(null); setPrintJob(null); setGuardOpen(false); setTicketOpen(false);
    setPaymentMethod("cod"); setPaymentReference(""); setTendered(0);
  }, [session?.id]);

  useEffect(() => {
    if (!order || !data?.foods) return;
    const lines = linesFromOrder(order, data.foods);
    setCart(lines); setSaved(lines);
  }, [order, data?.foods]);

  useEffect(() => { if (screen === "invoice") setTendered(due); }, [screen, due]);
  useEffect(() => { const id = window.setInterval(() => setTick((t) => t + 1), 30_000); return () => window.clearInterval(id); }, []);

  useEffect(() => {
    if (!printJob) return;
    const timer = window.setTimeout(() => window.print(), 180);
    const reset = () => setPrintJob(null);
    window.addEventListener("afterprint", reset, { once: true });
    return () => { window.clearTimeout(timer); window.removeEventListener("afterprint", reset); };
  }, [printJob]);

  // Bàn chưa có món nào gửi bếp (hoặc hoá đơn đã bị huỷ): thoát ra thì đề nghị giải phóng bàn,
  // tránh bàn trống mà vẫn hiện "đang dùng" và đếm giờ.
  const releasable = canOperate && current?.status === "active" && ((cart.length === 0 && !sentToKitchen) || order?.status === "cancelled");
  const requestClose = useCallback(() => {
    if (releasable) setReleaseOpen(true);
    else if (dirty && editable) setGuardOpen(true);
    else onClose();
  }, [releasable, dirty, editable, onClose]);

  useEffect(() => {
    if (!session) return;
    const onKey = (event: KeyboardEvent) => {
      const typing = event.target instanceof HTMLElement && ["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName);
      if (event.key === "Escape") {
        if (guardOpen) return setGuardOpen(false);
        if (releaseOpen) return setReleaseOpen(false);
        if (typing && event.target === searchRef.current && search) return setSearch("");
        if (screen === "invoice") return setScreen("menu");
        requestClose();
      } else if (event.key === "/" && !typing && screen === "menu") {
        event.preventDefault();
        searchRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [session, guardOpen, releaseOpen, search, screen, requestClose]);

  const refresh = async () => { await refetch(); onChanged(); };

  const addFood = (food: AdminFood) => {
    if (!editable) return;
    setCart((rows) => {
      const found = rows.findIndex((line) => line.foodId === food.id && !line.note.trim());
      if (found < 0) return [...rows, { foodId: food.id, name: food.name, category: food.category, price: food.price, image: food.image, qty: 1, note: "" }];
      return rows.map((line, index) => index === found ? { ...line, qty: line.qty + 1 } : line);
    });
  };
  const changeQuantity = (index: number, delta: number) => setCart((rows) => rows.flatMap((line, i) => {
    if (i !== index) return [line];
    const qty = line.qty + delta;
    return qty > 0 ? [{ ...line, qty }] : [];
  }));
  const setNote = (index: number, note: string) => setCart((rows) => rows.map((line, i) => i === index ? { ...line, note } : line));

  const saveCart = async (): Promise<string | null | false> => {
    if (!current) return false;
    if (cart.some((line) => !line.foodId)) {
      push("Một món trong phiếu không còn trong thực đơn. Xoá món đó rồi thử lại.", "err");
      return false;
    }
    setBusy(true);
    try {
      const res = await replaceDiningSessionItems(current.id, cart.map((line) => ({ foodId: line.foodId, quantity: line.qty, note: line.note.trim() })));
      if (sentToKitchen && res.lowStock.length) push(lowStockMessage(res.lowStock), "warn");
      const orderId = res.orderId ?? null;
      const savedOrder = orderId ? (await ordersStore.list()).find((item) => item.id === orderId) : undefined;
      const lines = savedOrder ? linesFromOrder(savedOrder, data?.foods ?? []) : [];
      setCart(lines); setSaved(lines);
      await refresh();
      return orderId;
    } catch (error) {
      push(error instanceof Error ? error.message : "Không lưu được phiếu gọi món.", "err");
      return false;
    } finally { setBusy(false); }
  };

  // Hoá đơn chỉ sinh ra ở bước này: lưu món (tạo hoá đơn nếu chưa có) rồi chuyển sang bếp.
  const sendToKitchen = async () => {
    const kot = newLines;
    if (!kot.length && !dirty) { push("Không có món mới để gửi bếp.", "err"); return false; }
    let orderId: string | null | undefined = order?.id;
    if (dirty) {
      const saved = await saveCart();
      if (saved === false) return false;
      orderId = saved;
    }
    setBusy(true);
    try {
      const latest = orderId ? (await ordersStore.list()).find((item) => item.id === orderId) : undefined;
      if (latest?.status === "pending") {
        const confirmed = await setOrderStatus(latest, "confirmed", "Gửi bếp từ màn gọi món");
        if (confirmed.lowStock.length) push(lowStockMessage(confirmed.lowStock), "warn");
      }
      await refresh();
      if (kot.length) {
        setPrintJob({ mode: "kot", lines: kot });
        push(`Đã gửi bếp ${kot.reduce((n, l) => n + l.qty, 0)} món. Đang mở phiếu bếp để in.`);
      } else push("Đã cập nhật phiếu gọi món.");
      return true;
    } catch (error) {
      push(error instanceof Error ? error.message : "Không gửi được món đến bếp.", "err");
      return false;
    } finally { setBusy(false); }
  };

  const openInvoice = async () => {
    if (!cart.length) return push("Phiếu chưa có món nào để thanh toán.", "err");
    if (!dirty || (await saveCart()) !== false) setScreen("invoice");
  };

  const printBill = async () => {
    if (!cart.length) return push("Phiếu chưa có món nào để in.", "err");
    if (!dirty || (await saveCart()) !== false) setPrintJob({ mode: "bill", lines: cart });
  };

  const advanceOrder = async () => {
    if (!order || !nextOrder) return;
    setBusy(true);
    try {
      await setOrderStatus(order, nextOrder.to);
      push(`Đơn ${order.code}: ${ORDER_META[nextOrder.to].label}`);
      await refresh();
    } catch (error) {
      push(error instanceof Error ? error.message : "Không cập nhật được trạng thái bếp.", "err");
    } finally { setBusy(false); }
  };

  const moveTable = async (targetTableId: string) => {
    if (!current || !targetTableId) return;
    setBusy(true);
    try {
      await moveDiningSession(current.id, targetTableId);
      push(`Đã chuyển sang ${tables.find((t) => t.id === targetTableId)?.number ?? "bàn mới"}.`);
      await refresh();
    } catch (error) {
      push(error instanceof Error ? error.message : "Không chuyển được bàn.", "err");
    } finally { setBusy(false); }
  };

  const confirmCleaned = async () => {
    if (!current) return;
    setBusy(true);
    try {
      await confirmDiningSessionCleaned(current.id);
      push(`Đã dọn xong ${current.tableLabel}. Bàn sẵn sàng đón khách.`);
      onChanged(); onClose();
    } catch (error) {
      push(error instanceof Error ? error.message : "Không xác nhận được đã dọn bàn.", "err");
    } finally { setBusy(false); }
  };

  const checkout = async () => {
    if (!current) return;
    setBusy(true);
    try {
      await checkoutDiningSession(current.id, paymentMethod, paymentReference);
      push(`Đã thu ${formatCurrency(due)}${deposit ? ` (đã trừ cọc ${formatCurrency(deposit)})` : ""}. ${current.tableLabel} đã trống.`);
      onChanged(); onClose();
    } catch (error) {
      push(error instanceof Error ? error.message : "Không hoàn tất được thanh toán.", "err");
    } finally { setBusy(false); }
  };

  const cancelTable = async () => {
    if (!current) return;
    setBusy(true);
    try {
      await cancelDiningSession(current.id, cancelReason.trim());
      push(sentToKitchen && order?.status !== "cancelled" ? `Đã huỷ hoá đơn ${order?.code ?? ""}. ${current.tableLabel} đã trống.` : `Đã giải phóng ${current.tableLabel}. Bàn đã trống.`);
      setCancelOpen(false); setReleaseOpen(false); onChanged(); onClose();
    } catch (error) {
      push(error instanceof Error ? error.message : "Không huỷ được bàn.", "err");
    } finally { setBusy(false); }
  };

  const closeFromGuard = async (action: "save" | "discard") => {
    if (action === "save" && !(await sendToKitchen())) return;
    setGuardOpen(false);
    onClose();
  };

  if (!session || !current) return null;
  const elapsed = current.status === "active" ? minutesSince(current.startedAt) : null;
  const guestLabel = current.customer || (current.reservationId ? "Khách đặt bàn" : "Khách vãng lai");

  return (
    <div className="fixed inset-0 z-60 flex flex-col bg-bg text-dark" role="dialog" aria-modal="true" aria-label={`Gọi món ${current.tableLabel}`}>
      {/* Thanh bàn: luôn cho biết đang thao tác ở bàn nào, khách nào. */}
      <header className="flex items-center gap-x-5 gap-y-1 bg-dark px-3 py-2.5 text-white sm:px-6 sm:py-3">
        <button onClick={screen === "invoice" ? () => setScreen("menu") : requestClose} className="inline-flex items-center gap-2 rounded-lg px-2 py-2 text-sm text-white/80 hover:bg-white/10 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent">
          <ArrowLeft size={18} /><span className="hidden whitespace-nowrap md:inline">{screen === "invoice" ? "Phiếu gọi món" : "Sơ đồ bàn"}</span>
        </button>
        <div className="flex min-w-0 flex-col sm:flex-row sm:items-baseline sm:gap-4">
          <h1 className="whitespace-nowrap font-display text-2xl font-bold tracking-tight sm:text-3xl">{current.tableLabel}</h1>
          <div className="min-w-0 truncate text-xs text-white/70 sm:text-sm">
            <span className="font-medium text-white">{guestLabel}</span>
            <span className="ml-3">{current.guestCount} khách</span>
            {elapsed && <span className="ml-3">ngồi {elapsed}</span>}
            {order && <span className="ml-3 hidden sm:inline">Đơn {order.code}</span>}
          </div>
        </div>
        <div className="ml-auto flex items-center gap-2">
          {editable && destinationTables.length > 0 && screen === "menu" && (
            <label className="relative">
              <span className="sr-only">Chuyển sang bàn khác</span>
              <select value="" disabled={busy} onChange={(event) => void moveTable(event.target.value)} className="h-10 max-w-28 rounded-lg sm:max-w-none border border-white/20 bg-white/5 px-3 pr-8 text-sm text-white focus:border-accent focus:outline-none">
                <option value="" className="text-dark">Chuyển bàn</option>
                {destinationTables.map((table) => <option key={table.id} value={table.id} className="text-dark">{table.number} ({table.capacity} ghế)</option>)}
              </select>
            </label>
          )}
          <button onClick={requestClose} aria-label="Đóng" className="flex h-10 w-10 items-center justify-center rounded-lg text-white/80 hover:bg-white/10 hover:text-white"><X size={20} /></button>
        </div>
      </header>

      {screen === "invoice" ? (
        <InvoiceView
          lines={cart} subtotal={subtotal} discount={discount} total={total} deposit={deposit} order={order} busy={busy}
          paymentMethod={paymentMethod} setPaymentMethod={setPaymentMethod}
          paymentReference={paymentReference} setPaymentReference={setPaymentReference}
          tendered={tendered} setTendered={setTendered}
          onBack={() => setScreen("menu")} onCheckout={() => void checkout()}
        />
      ) : (
        <div className="flex min-h-0 flex-1 flex-col lg:grid lg:grid-cols-[minmax(0,1fr)_minmax(340px,400px)]">
          {/* Thực đơn */}
          <section className="flex min-h-0 flex-1 flex-col" aria-label="Thực đơn">
            <div className="space-y-3 border-b border-black/[0.07] px-4 pb-0 pt-4 sm:px-6">
              <label className="relative block max-w-xl">
                <span className="sr-only">Tìm món</span>
                <Search size={17} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                <input ref={searchRef} value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Tìm món" className={`${inputCls} pl-10! pr-10!`} />
                <kbd className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 rounded border border-black/10 px-1.5 text-xs text-muted">/</kbd>
              </label>
              <nav className="-mb-px flex gap-1 overflow-x-auto" aria-label="Danh mục món">
                {categories.map((item) => {
                  const active = category === item;
                  return <button key={item} onClick={() => setCategory(item)} aria-pressed={active} className={`shrink-0 border-b-2 px-3 pb-2.5 pt-1 text-sm font-medium transition-colors ${active ? "border-primary text-primary" : "border-transparent text-muted hover:text-dark"}`}>{item}</button>;
                })}
              </nav>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto p-4 sm:p-6">
              {loading ? (
                <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 xl:grid-cols-4">{Array.from({ length: 12 }, (_, i) => <div key={i} className="h-[88px] animate-pulse rounded-xl bg-black/[0.05]" />)}</div>
              ) : visibleFoods.length ? (
                <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
                  {visibleFoods.map((food) => {
                    const qty = qtyByFood.get(food.id) ?? 0;
                    const short = shortFoods.get(food.name);
                    return (
                      <button key={food.id} type="button" disabled={!editable || busy} onClick={() => addFood(food)} aria-label={`Thêm ${food.name}, ${formatCurrency(food.price)}${qty ? `, đang có ${qty}` : ""}`}
                        className={`relative flex min-h-[88px] items-start gap-3 rounded-xl border bg-white p-3 text-left transition-[border-color,box-shadow] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary ${qty ? "border-primary/60 shadow-[inset_0_0_0_1px_var(--color-primary)]" : "border-black/[0.08] hover:border-black/20"}`}>
                        {food.image && <img src={food.image} alt="" className="h-14 w-14 shrink-0 rounded-lg object-cover" loading="lazy" onError={(e) => { e.currentTarget.style.display = "none"; }} />}
                        <span className="flex min-w-0 flex-1 flex-col self-stretch">
                          <span className="line-clamp-2 pr-6 text-sm font-medium leading-snug">{food.name}</span>
                          <span className="mt-auto flex items-center gap-2 pt-1 text-sm tabular-nums text-muted">{formatCurrency(food.price)}{short && <span title={short.join(", ")} className="rounded bg-secondary/25 px-1.5 py-0.5 text-[11px] font-medium text-[#8a6416]">Sắp hết NL</span>}</span>
                        </span>
                        {qty > 0 && <span className="absolute right-2 top-2 flex h-6 min-w-6 items-center justify-center rounded-full bg-primary px-1.5 text-xs font-semibold tabular-nums text-white">{qty}</span>}
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="py-16 text-center text-sm text-muted">
                  Không có món nào khớp “{search}”.
                  {search && <button onClick={() => setSearch("")} className="ml-2 font-medium text-primary hover:underline">Xoá tìm kiếm</button>}
                </div>
              )}
            </div>
          </section>

          {/* Phiếu gọi món: món đã gửi bếp và món mới thêm được tách bằng màu viền. */}
          <aside className={`flex min-h-0 flex-col border-t border-black/[0.07] bg-[#fffdf8] max-lg:shadow-[0_-8px_24px_rgb(38_42_37/10%)] lg:border-l lg:border-t-0 ${ticketOpen ? "max-lg:max-h-[78vh]" : ""}`} aria-label="Phiếu gọi món">
            <button type="button" onClick={() => setTicketOpen((v) => !v)} aria-expanded={ticketOpen} className="flex w-full items-center justify-between px-5 pt-3 text-sm font-medium lg:hidden">
              <span>{itemCount ? `Phiếu: ${itemCount} món` : "Phiếu trống"}{newCount > 0 && <span className="ml-2 text-[#8a6416]">{newCount} chưa gửi bếp</span>}</span>
              <span className="text-primary">{ticketOpen ? "Thu gọn" : "Xem phiếu"}</span>
            </button>
            <div className={`items-start justify-between gap-3 px-5 pb-3 pt-4 ${ticketOpen ? "flex" : "hidden lg:flex"}`}>
              <div>
                <h2 className="font-display text-lg font-semibold">Phiếu gọi món</h2>
                <p className="text-sm text-muted">{itemCount ? `${itemCount} món` : "Chưa có món"}{order && <span className="ml-3">Bếp: {ORDER_META[order.status].label.toLowerCase()}</span>}</p>
              </div>
              {nextOrder && sentToKitchen && canOperate && <button disabled={busy} onClick={() => void advanceOrder()} className="shrink-0 rounded-lg border border-black/10 px-2.5 py-1.5 text-xs font-medium hover:border-primary hover:text-primary">{nextOrder.label}</button>}
            </div>

            <ol className={`min-h-0 flex-1 overflow-y-auto px-3 ${ticketOpen ? "" : "max-lg:hidden"}`}>
              {cart.length === 0 ? (
                <li className="mx-2 rounded-xl border border-dashed border-black/15 px-4 py-10 text-center text-sm text-muted">Chạm vào món trong thực đơn để thêm vào phiếu.</li>
              ) : cart.map((line, index) => {
                const fresh = newQtyOf(line);
                const key = `${lineKey(line)}-${index}`;
                return (
                  <li key={key} className={`mb-1.5 rounded-lg border-l-[3px] bg-white px-3 py-2.5 ${fresh ? "border-secondary" : "border-success"}`}>
                    <div className="flex items-start gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-medium leading-snug">{line.name}</div>
                        <div className="mt-0.5 text-xs text-muted tabular-nums">
                          {formatCurrency(line.price)}
                          {fresh > 0 ? <span className="ml-2 font-medium text-[#8a6416]">{sentToKitchen ? `+${fresh} chưa gửi bếp` : "Chưa gửi bếp"}</span> : <span className="ml-2 text-success">Đã gửi bếp</span>}
                        </div>
                        {line.note && noteOpen !== key && <div className="mt-1 text-xs italic text-dark/70">“{line.note}”</div>}
                      </div>
                      <div className="text-right text-sm font-semibold tabular-nums">{formatCurrency(line.price * line.qty)}</div>
                    </div>
                    {editable && (
                      <div className="mt-2 flex items-center gap-2">
                        <div className="inline-flex items-center rounded-lg border border-black/10">
                          <button onClick={() => changeQuantity(index, -1)} disabled={!isManager && sentToKitchen && line.qty <= (savedQty.get(lineKey(line)) ?? 0)}
                            title={!isManager && sentToKitchen && line.qty <= (savedQty.get(lineKey(line)) ?? 0) ? "Món đã gửi bếp: cần quản lý chi nhánh bớt" : undefined}
                            aria-label={`Bớt ${line.name}`} className="flex h-9 w-9 items-center justify-center text-dark/70 hover:text-primary disabled:cursor-not-allowed disabled:opacity-30"><Minus size={15} /></button>
                          <span className="w-7 text-center text-sm font-semibold tabular-nums" aria-live="polite">{line.qty}</span>
                          <button onClick={() => changeQuantity(index, 1)} aria-label={`Thêm ${line.name}`} className="flex h-9 w-9 items-center justify-center text-dark/70 hover:text-primary"><Plus size={15} /></button>
                        </div>
                        <button onClick={() => setNoteOpen(noteOpen === key ? null : key)} className="inline-flex h-9 items-center gap-1.5 rounded-lg px-2.5 text-xs text-muted hover:bg-black/[0.04] hover:text-dark"><NotebookPen size={14} />{line.note ? "Sửa ghi chú" : "Ghi chú"}</button>
                      </div>
                    )}
                    {noteOpen === key && <textarea autoFocus value={line.note} onChange={(event) => setNote(index, event.target.value)} onBlur={() => setNoteOpen(null)} rows={2} maxLength={300} placeholder="Ít cay, không hành…" className="mt-2 w-full resize-none rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-primary" />}
                  </li>
                );
              })}
            </ol>

            <div className="space-y-3 border-dashed border-black/15 px-5 pb-4 pt-3 lg:border-t lg:pb-5 lg:pt-4">
              {discount > 0 && <Amount label="Giảm giá" value={`− ${formatCurrency(discount)}`} />}
              <div className="flex items-baseline justify-between">
                <span className="text-sm text-muted">Tạm tính</span>
                <span className="font-display text-2xl font-bold tabular-nums">{formatCurrency(total)}</span>
              </div>
              {deposit > 0 && <p className="-mt-2 text-right text-xs text-muted tabular-nums">Đã cọc {formatCurrency(deposit)}, còn thu {formatCurrency(due)}</p>}
              {orderClosed && order && <p className="rounded-lg bg-black/[0.05] px-3 py-2 text-xs text-dark/80">Đơn {order.code} đã {order.status === "cancelled" ? "bị huỷ" : "hoàn tất"}, nên không thêm hay sửa món được nữa.</p>}
              {order?.status === "cancelled" && canOperate && current.status === "active" && <button disabled={busy} onClick={() => void cancelTable()} className="btn btn-primary w-full py-3!">Giải phóng bàn</button>}
              {reducedSent && <p className="rounded-lg bg-primary/10 px-3 py-2 text-xs text-primary-dark">Bạn đã bớt món đã gửi bếp. Báo bếp trực tiếp để huỷ phần đó.</p>}
              {order?.status === "cancelled" ? null : current.status === "cleaning" ? (
                <button disabled={busy} onClick={() => void confirmCleaned()} className="btn w-full bg-secondary! py-3! text-dark!"><Check size={17} />Đã dọn xong bàn</button>
              ) : (
                <>
                  <button disabled={busy || !editable || (!newCount && !dirty)} onClick={() => void sendToKitchen()} className="btn btn-primary w-full py-3! text-[15px]! disabled:opacity-45">
                    <ChefHat size={18} />{busy ? "Đang gửi…" : newCount ? `Gửi bếp ${newCount} món` : dirty ? "Cập nhật phiếu" : sentToKitchen ? "Đã gửi bếp đủ món" : "Gửi bếp"}
                  </button>
                  <div className="grid grid-cols-2 gap-2">
                    <button disabled={busy || !cart.length} onClick={() => void printBill()} className="btn btn-outline py-2.5! disabled:opacity-45"><Printer size={16} />In tạm tính</button>
                    <button disabled={busy || !cart.length || !canOperate} onClick={() => void openInvoice()} className="btn bg-dark! py-2.5! text-white! hover:bg-black! disabled:opacity-45">Thanh toán</button>
                  </div>
                  {editable && (!sentToKitchen || isManager) && (
                    <button disabled={busy} onClick={() => { setCancelReason(""); setCancelOpen(true); }} className="w-full text-center text-xs font-medium text-primary/80 hover:text-primary">
                      {sentToKitchen ? "Huỷ hoá đơn (quản lý)" : "Huỷ bàn, khách không dùng bữa"}
                    </button>
                  )}
                  {editable && sentToKitchen && !isManager && <p className="text-center text-xs text-muted">Bớt món hoặc huỷ hoá đơn đã gửi bếp cần quản lý chi nhánh.</p>}
                </>
              )}
            </div>
          </aside>
        </div>
      )}

      <ConfirmModal
        open={cancelOpen} danger busy={busy}
        title={sentToKitchen ? `Huỷ hoá đơn ${order?.code ?? ""}?` : `Huỷ ${current.tableLabel}?`}
        message={sentToKitchen ? "Hoá đơn chuyển sang Đã huỷ, nguyên liệu đã xuất được hoàn lại kho, bàn trở về trống." : "Bàn trở về trống. Các món chưa gửi bếp bị bỏ, không tạo hoá đơn."}
        confirmLabel={sentToKitchen ? "Huỷ hoá đơn" : "Huỷ bàn"}
        onConfirm={() => void cancelTable()} onCancel={() => setCancelOpen(false)}
      >
        {sentToKitchen && <>
          <label className="mb-1.5 block text-[13px] font-semibold text-muted" htmlFor="cancel-reason">Lý do huỷ</label>
          <input id="cancel-reason" value={cancelReason} onChange={(e) => setCancelReason(e.target.value)} className={inputCls} placeholder="Ví dụ: khách đổi ý, gọi nhầm bàn" />
        </>}
      </ConfirmModal>

      {releaseOpen && (
        <div className="fixed inset-0 z-[70] flex items-center justify-center bg-dark/40 p-4" role="presentation" onMouseDown={(e) => { if (e.target === e.currentTarget) setReleaseOpen(false); }}>
          <div role="alertdialog" aria-modal="true" aria-labelledby="release-title" className="w-full max-w-sm rounded-2xl bg-white p-5 shadow-lift">
            <h2 id="release-title" className="font-display text-lg font-semibold">{order?.status === "cancelled" ? `Hoá đơn ${order.code} đã bị huỷ` : `${current?.tableLabel ?? "Bàn"} chưa gọi món`}</h2>
            <p className="mt-1.5 text-sm text-muted">{order?.status === "cancelled" ? "Giải phóng bàn để đón khách khác." : "Chưa có món nào gửi bếp. Giải phóng bàn để đón khách khác, hoặc giữ bàn nếu khách vẫn đang xem thực đơn."}</p>
            <div className="mt-5 flex flex-col gap-2">
              <button disabled={busy} onClick={() => void cancelTable()} className="btn btn-primary py-2.5!">{busy ? "Đang giải phóng…" : "Giải phóng bàn"}</button>
              {order?.status !== "cancelled" && <button disabled={busy} onClick={() => { setReleaseOpen(false); onClose(); }} className="btn btn-outline py-2.5!">Giữ bàn, khách đang chọn món</button>}
              <button onClick={() => setReleaseOpen(false)} className="py-2 text-sm text-muted hover:text-dark">Ở lại</button>
            </div>
          </div>
        </div>
      )}

      {guardOpen && (
        <div className="fixed inset-0 z-[70] flex items-center justify-center bg-dark/40 p-4" role="presentation" onMouseDown={(e) => { if (e.target === e.currentTarget) setGuardOpen(false); }}>
          <div role="alertdialog" aria-modal="true" aria-labelledby="guard-title" className="w-full max-w-sm rounded-2xl bg-white p-5 shadow-lift">
            <h2 id="guard-title" className="font-display text-lg font-semibold">Phiếu còn món chưa gửi bếp</h2>
            <p className="mt-1.5 text-sm text-muted">Nếu đóng bây giờ, các thay đổi ở {current.tableLabel} sẽ mất.</p>
            <div className="mt-5 flex flex-col gap-2">
              <button disabled={busy} onClick={() => void closeFromGuard("save")} className="btn btn-primary py-2.5!">Gửi bếp rồi đóng</button>
              <button disabled={busy} onClick={() => void closeFromGuard("discard")} className="btn btn-outline py-2.5! text-primary!">Bỏ thay đổi</button>
              <button onClick={() => setGuardOpen(false)} className="py-2 text-sm text-muted hover:text-dark">Ở lại</button>
            </div>
          </div>
        </div>
      )}

      {printJob && <>
        <style>{`@media print { body * { visibility: hidden !important; } [data-pos-print], [data-pos-print] * { visibility: visible !important; } [data-pos-print] { display: block !important; position: fixed !important; inset: 0 !important; width: 100% !important; background: white !important; color: black !important; padding: 24px !important; } }`}</style>
        <section data-pos-print className="hidden text-black">
          <h1 className="text-xl font-bold">{printJob.mode === "kot" ? "PHIẾU BẾP" : "HOÁ ĐƠN TẠM TÍNH"}</h1>
          <p className="mt-2">{current.tableLabel} · {guestLabel} · {current.guestCount} khách · {order?.code}</p>
          <hr className="my-3" />
          {printJob.lines.map((line, index) => <div key={`${line.foodId}-${index}`} className="mb-3"><div className="flex justify-between"><span>{line.qty} × {line.name}</span>{printJob.mode === "bill" && <span>{formatCurrency(line.qty * line.price)}</span>}</div>{line.note && <p className="text-sm">Ghi chú: {line.note}</p>}</div>)}
          {printJob.mode === "bill" && <><hr className="my-3" /><p>Tạm tính: {formatCurrency(subtotal)}</p>{discount > 0 && <p>Giảm giá: {formatCurrency(discount)}</p>}<p className="mt-2 font-bold">Tổng cộng: {formatCurrency(total)}</p></>}
          <p className="mt-6 text-xs">{new Date().toLocaleString("vi-VN")}</p>
        </section>
      </>}
    </div>
  );
}

interface InvoiceProps {
  lines: CartLine[]; subtotal: number; discount: number; total: number; deposit: number; order?: AdminOrder; busy: boolean;
  paymentMethod: "cod" | "bank"; setPaymentMethod: (m: "cod" | "bank") => void;
  paymentReference: string; setPaymentReference: (v: string) => void;
  tendered: number; setTendered: (v: number) => void;
  onBack: () => void; onCheckout: () => void;
}

function InvoiceView({ lines, subtotal, discount, total: billTotal, deposit, order, busy, paymentMethod, setPaymentMethod, paymentReference, setPaymentReference, tendered, setTendered, onBack, onCheckout }: InvoiceProps) {
  const total = billTotal - deposit; // số tiền còn phải thu
  const quick = [total, Math.ceil(total / 50000) * 50000, Math.ceil(total / 100000) * 100000, Math.ceil(total / 500000) * 500000].filter((v, i, all) => v > 0 && all.indexOf(v) === i);
  const change = Math.max(0, tendered - total);
  const short = paymentMethod === "cod" && tendered < total;
  return (
    <div className="grid min-h-0 flex-1 grid-cols-1 overflow-y-auto lg:grid-cols-[minmax(0,1fr)_minmax(340px,420px)]">
      <section className="px-4 py-6 sm:px-8" aria-label="Món trong hoá đơn">
        <h2 className="font-display text-lg font-semibold">Hoá đơn {order?.code}</h2>
        <table className="mt-4 w-full max-w-2xl text-sm">
          <tbody>
            {lines.map((line, index) => (
              <tr key={`${line.foodId}-${index}`} className="border-b border-black/[0.06] align-top">
                <td className="w-10 py-3 tabular-nums text-muted">{line.qty}×</td>
                <td className="py-3"><div className="font-medium">{line.name}</div>{line.note && <div className="text-xs italic text-muted">“{line.note}”</div>}</td>
                <td className="py-3 text-right tabular-nums">{formatCurrency(line.qty * line.price)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="flex flex-col gap-5 border-t border-black/[0.07] bg-[#fffdf8] px-5 py-6 lg:border-l lg:border-t-0" aria-label="Thanh toán">
        <div className="space-y-2 text-sm">
          <Amount label="Tiền món" value={formatCurrency(subtotal)} />
          {discount > 0 && <Amount label="Giảm giá" value={`− ${formatCurrency(discount)}`} />}
          {deposit > 0 && <Amount label="Đã đặt cọc" value={`− ${formatCurrency(deposit)}`} />}
          <div className="flex items-baseline justify-between border-t border-dashed border-black/15 pt-3">
            <span className="text-muted">Khách cần trả</span>
            <span className="font-display text-3xl font-bold tabular-nums">{formatCurrency(total)}</span>
          </div>
        </div>
        <fieldset>
          <legend className="mb-2 text-sm font-medium">Hình thức</legend>
          <div className="grid grid-cols-2 gap-2">
            {([["cod", "Tiền mặt"], ["bank", "Chuyển khoản"]] as const).map(([value, label]) => (
              <label key={value} className={`cursor-pointer rounded-lg border px-3 py-2.5 text-center text-sm font-medium has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-primary ${paymentMethod === value ? "border-dark bg-dark text-white" : "border-black/10 bg-white hover:border-black/25"}`}>
                <input type="radio" name="payment-method" value={value} checked={paymentMethod === value} onChange={() => setPaymentMethod(value)} className="sr-only" />{label}
              </label>
            ))}
          </div>
        </fieldset>
        {paymentMethod === "cod" ? (
          <div>
            <label className="block text-sm font-medium">Khách đưa
              <input type="number" min={0} step={1000} value={tendered || ""} onChange={(event) => setTendered(Number(event.target.value) || 0)} className={`${inputCls} mt-1.5 text-right text-xl font-semibold tabular-nums`} />
            </label>
            <div className="mt-2 flex flex-wrap gap-1.5">{quick.map((amount) => <button key={amount} onClick={() => setTendered(amount)} className={`rounded-md px-2.5 py-1.5 text-xs tabular-nums ${tendered === amount ? "bg-dark text-white" : "bg-black/[0.05] hover:bg-black/10"}`}>{formatCurrency(amount)}</button>)}</div>
            <div className="mt-4 flex items-baseline justify-between text-sm"><span className="text-muted">Tiền thối</span><span className="text-lg font-semibold tabular-nums">{formatCurrency(change)}</span></div>
            {short && <p className="mt-1 text-xs text-primary">Còn thiếu {formatCurrency(total - tendered)}.</p>}
          </div>
        ) : (
          <label className="block text-sm font-medium">Mã giao dịch
            <input value={paymentReference} onChange={(event) => setPaymentReference(event.target.value)} className={`${inputCls} mt-1.5`} placeholder="Không bắt buộc" />
          </label>
        )}
        <div className="mt-auto flex gap-2 pt-2">
          <button onClick={onBack} className="btn btn-outline flex-1 py-3!">Quay lại</button>
          <button disabled={busy || short} onClick={onCheckout} className="btn btn-primary flex-[2] py-3! disabled:opacity-45"><Check size={17} />{busy ? "Đang thanh toán…" : total > 0 ? `Thu ${formatCurrency(total)}` : "Hoàn tất, không thu thêm"}</button>
        </div>
      </section>
    </div>
  );
}

function Amount({ label, value }: { label: string; value: string }) {
  return <div className="flex items-center justify-between gap-3"><span className="text-muted">{label}</span><span className="font-medium tabular-nums">{value}</span></div>;
}
