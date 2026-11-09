import { useCallback, useEffect, useMemo, useState } from "react";
import { Archive, Brush, Building2, CalendarCheck, CalendarClock, ChevronDown, CircleAlert, DoorOpen, Minus, Pencil, Plus, RefreshCw, RotateCcw, Search, Settings2, Sparkles, Wrench, X } from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency } from "@/lib/utils";
import RecordDrawer, { type FieldDef } from "../components/RecordDrawer";
import DiningSessionDrawer from "../components/DiningSessionDrawer";
import ConfirmModal from "../components/ConfirmModal";
import { PageHeader, inputCls } from "../components/primitives";
import { useToast } from "../components/toast";
import { TABLE_META } from "../statusMeta";
import { useCan } from "../permissions";
import { ymd } from "../lib";
import type { AdminBranch } from "../data/mockCatalog";
import type { AdminDiningSession, AdminPrivateRoom, AdminReservation, AdminTable, TableStatus } from "../types";
import {
  archiveTableManagementRoom,
  archiveTableManagementTable,
  checkInReservation,
  createTableManagementRoom,
  createTableManagementTable,
  getTableManagementBranches,
  getTableManagementRooms,
  getTableManagementTables,
  reservationsStore,
  restoreTableManagementTable,
  startReservationSession,
  startWalkIn,
  updateTableManagementRoom,
  updateTableManagementTable,
} from "../api/admin.api";

type Mode = "operate" | "configure";
type StatusFilter = "all" | "available" | "busy";
const ALL_AREAS = "Tất cả";
const OPEN_MENU_KEY = "moc.tables.openMenuOnSelect";

const statusOptions = (Object.keys(TABLE_META) as TableStatus[])
  .filter((s) => s !== "occupied" && s !== "cleaning")
  .map((s) => ({ value: s, label: TABLE_META[s].label }));
const tableFields = (rooms: AdminPrivateRoom[]): FieldDef<AdminTable>[] => [
  { key: "number", label: "Tên bàn", type: "text", required: true },
  { key: "zone", label: "Khu vực / tầng", type: "text", required: true, hint: "Ví dụ: Trong nhà - Tầng 1, Sân vườn - Ngoài trời." },
  { key: "capacity", label: "Sức chứa (ghế)", type: "number", required: true },
  { key: "status", label: "Trạng thái", type: "select", required: true, options: statusOptions },
  { key: "roomId", label: "Phòng riêng", type: "select", options: [{ value: "", label: "Không thuộc phòng riêng" }, ...rooms.map((r) => ({ value: r.id, label: `${r.name}${r.floor ? ` · ${r.floor}` : ""}` }))] },
];

const branchBlankTable = (branchId = ""): Partial<AdminTable> => ({ branchId, number: "", zone: "Trong nhà - Tầng 1", capacity: 4, status: "available", roomId: "" });
/** Tab khu vực: bàn thuộc phòng riêng gom vào một tab, còn lại theo đúng tên khu vực đã nhập. */
const areaOf = (t: AdminTable) => (t.roomId ? "Phòng riêng" : t.zone.trim() || "Khu vực chung");
const byNumber = (a: AdminTable, b: AdminTable) => a.number.localeCompare(b.number, "vi", { numeric: true });

/** Bàn đang có khách ngồi (phiên mở) — gồm cả trạng thái giữ/đặt do backend trả về. */
const isBusy = (t: AdminTable) => (t.activeSession?.status === "active") || ["occupied", "held", "reserved"].includes(t.status);
const isCleaning = (t: AdminTable) => t.status === "cleaning" || t.activeSession?.status === "cleaning";
const isFree = (t: AdminTable) => !t.archived && !t.activeSession && t.status === "available";

function minutesSince(iso: string | undefined, now: number) {
  if (!iso) return null;
  const started = new Date(iso).getTime();
  return Number.isNaN(started) ? null : Math.max(0, Math.floor((now - started) / 60000));
}
const fmtDuration = (m: number) => (m < 60 ? `${m}'` : m < 1440 ? `${Math.floor(m / 60)}h${String(m % 60).padStart(2, "0")}` : `${Math.floor(m / 1440)} ngày`);
/** Số phút khách đến muộn so với giờ hẹn hôm nay (âm = còn sớm). */
function lateMinutes(time: string, now: number) {
  const [h, m] = time.split(":").map(Number);
  if (Number.isNaN(h)) return 0;
  const d = new Date(now); d.setHours(h, m || 0, 0, 0);
  return Math.floor((now - d.getTime()) / 60000);
}

export default function TablesPage() {
  const user = useAuthStore((s) => s.nguoiDung);
  const isAdmin = Boolean(user?.laQuanTri || user?.danhSachVaiTro?.some((r) => r === "admin" || r === "quan_tri_vien"));
  const push = useToast((s) => s.push);
  const can = useCan();
  const canConfigure = can("tables", "update");
  const canOperate = can("reservations", "update");
  const [mode, setMode] = useState<Mode>("operate");
  const [branches, setBranches] = useState<AdminBranch[]>([]);
  const [selectedBranch, setSelectedBranch] = useState(isAdmin ? "all" : "");
  const [tables, setTables] = useState<AdminTable[]>([]);
  const [rooms, setRooms] = useState<AdminPrivateRoom[]>([]);
  const [reservations, setReservations] = useState<AdminReservation[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [editingTable, setEditingTable] = useState<AdminTable | "new" | null>(null);
  const [editingRoom, setEditingRoom] = useState<AdminPrivateRoom | "new" | null>(null);
  const [saving, setSaving] = useState(false);
  const [areaFilter, setAreaFilter] = useState(ALL_AREAS);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [search, setSearch] = useState("");
  const [walkInTable, setWalkInTable] = useState<AdminTable | null>(null);
  const [openSession, setOpenSession] = useState<AdminDiningSession | null>(null);
  const [seating, setSeating] = useState<AdminReservation | null>(null);
  const [seatTarget, setSeatTarget] = useState<AdminTable | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [openMenuOnSelect, setOpenMenuOnSelect] = useState(() => { try { return localStorage.getItem(OPEN_MENU_KEY) !== "0"; } catch { return true; } });
  const toggleOpenMenu = (on: boolean) => { setOpenMenuOnSelect(on); try { localStorage.setItem(OPEN_MENU_KEY, on ? "1" : "0"); } catch { /* bỏ qua */ } };
  const selectedBranchData = branches.find((b) => b.id === selectedBranch);

  useEffect(() => { const id = window.setInterval(() => setNow(Date.now()), 30_000); return () => window.clearInterval(id); }, []);

  const loadBranches = useCallback(async () => {
    try {
      const rows = await getTableManagementBranches();
      setBranches(rows);
      if (!isAdmin && rows.length) setSelectedBranch(rows[0].id);
      if (!isAdmin && rows.length === 0) {
        setLoading(false);
        setLoadError("Tài khoản chưa được gán chi nhánh. Quản trị viên cần chọn chi nhánh phụ trách trong mục Người dùng.");
      } else setLoadError("");
    } catch {
      setLoading(false);
      setLoadError("Không tải được danh sách chi nhánh.");
    }
  }, [isAdmin]);

  useEffect(() => { void loadBranches(); }, [loadBranches]);

  const loadBranchData = useCallback(async (quiet = false) => {
    if (!quiet) { setLoading(true); setLoadError(""); }
    const branchId = selectedBranch === "all" ? undefined : selectedBranch || undefined;
    try {
      const [tableRows, roomRows, reservationRows] = await Promise.all([
        getTableManagementTables(branchId, includeArchived),
        getTableManagementRooms(branchId),
        canOperate ? reservationsStore.list().catch(() => [] as AdminReservation[]) : Promise.resolve([] as AdminReservation[]),
      ]);
      setTables(tableRows.map((table) => {
        const room = roomRows.find((candidate) => candidate.id === table.roomId);
        return room ? { ...table, roomName: room.name, zone: room.floor || table.zone } : table;
      }));
      setRooms(roomRows);
      setReservations(reservationRows);
    } catch {
      if (!quiet) { setTables([]); setRooms([]); setLoadError("Không tải được sơ đồ bàn. Kiểm tra quyền chi nhánh rồi thử tải lại."); }
    } finally {
      if (!quiet) setLoading(false);
    }
  }, [selectedBranch, includeArchived, canOperate]);

  useEffect(() => { if (selectedBranch || isAdmin) void loadBranchData(); }, [loadBranchData, selectedBranch, isAdmin]);

  // Tự làm mới nhẹ để quầy lễ tân thấy bàn vừa trống / khách vừa đến.
  const idle = !walkInTable && !openSession && !seatTarget && !editingTable && !editingRoom;
  useEffect(() => {
    if (!idle || (!selectedBranch && !isAdmin)) return;
    const id = window.setInterval(() => void loadBranchData(true), 30_000);
    return () => window.clearInterval(id);
  }, [idle, loadBranchData, selectedBranch, isAdmin]);

  const branchName = (id?: string) => branches.find((b) => b.id === id)?.name ?? "Chi nhánh";
  const activeTables = tables.filter((t) => !t.archived);
  const counts = {
    all: activeTables.length,
    available: activeTables.filter(isFree).length,
    busy: activeTables.filter((t) => isBusy(t) || isCleaning(t)).length,
  };
  const guestsSeated = activeTables.reduce((sum, t) => sum + (t.activeSession?.status === "active" ? t.activeSession.guestCount : 0), 0);
  const areas = [...new Set(activeTables.map(areaOf))].sort((a, b) => a.localeCompare(b, "vi", { numeric: true }));

  const today = ymd(0);
  const arrivals = useMemo(() => reservations
    .filter((r) => r.date === today && (r.status === "confirmed" || (r.status === "seated" && !r.sessionId)))
    .filter((r) => selectedBranch === "all" || !selectedBranch || r.branchId === selectedBranch)
    .sort((a, b) => a.time.localeCompare(b.time)), [reservations, today, selectedBranch]);
  const pendingToday = reservations.filter((r) => r.date === today && r.status === "pending_confirmation" && (selectedBranch === "all" || r.branchId === selectedBranch)).length;

  const fitsSeating = useCallback((t: AdminTable) => !!seating && isFree(t) && t.capacity >= seating.partySize && (!seating.branchId || t.branchId === seating.branchId), [seating]);
  const seatingFits = useMemo(() => activeTables.filter(fitsSeating).sort((a, b) => a.capacity - b.capacity), [activeTables, fitsSeating]);
  const suggestedId = seatingFits[0]?.id;

  const visibleTables = tables.filter((table) => {
    const matchesArea = areaFilter === ALL_AREAS || areaOf(table) === areaFilter;
    const matchesStatus = statusFilter === "all"
      || (statusFilter === "available" && isFree(table))
      || (statusFilter === "busy" && (isBusy(table) || isCleaning(table)));
    const q = search.trim().toLowerCase();
    const matchesSearch = !q || `${table.number} ${table.zone} ${table.roomName ?? ""} ${table.activeSession?.customer ?? ""} ${branchName(table.branchId)}`.toLowerCase().includes(q);
    return matchesArea && matchesStatus && matchesSearch;
  }).sort(byNumber);

  const tablesByBranch = useMemo(() => {
    const grouped = new Map<string, AdminTable[]>();
    for (const table of visibleTables) {
      const key = table.branchId ?? "unknown";
      grouped.set(key, [...(grouped.get(key) ?? []), table]);
    }
    return [...grouped.entries()];
  }, [visibleTables]);

  const fields = useMemo(() => tableFields(rooms.filter((r) => (selectedBranch === "all" || r.branchId === selectedBranch) && r.active)), [rooms, selectedBranch]);
  const tableInitial = useMemo(() => editingTable === "new" ? branchBlankTable(selectedBranch === "all" ? "" : selectedBranch) : editingTable ?? branchBlankTable(), [editingTable, selectedBranch]);

  const switchMode = (next: Mode) => { setMode(next); setSeating(null); if (next === "operate") setIncludeArchived(false); };

  const saveTable = async (values: Partial<AdminTable>) => {
    if (!values.branchId) return push("Chọn chi nhánh trước khi lưu bàn.", "err");
    setSaving(true);
    try {
      if (editingTable === "new") await createTableManagementTable({ ...branchBlankTable(values.branchId), ...values } as Omit<AdminTable, "id">);
      else if (editingTable) await updateTableManagementTable({ ...editingTable, ...values } as AdminTable);
      setEditingTable(null);
      push("Đã lưu bàn.");
      await loadBranchData();
    } catch {
      push("Không thể lưu bàn. Kiểm tra tên bàn, sức chứa và chi nhánh.", "err");
    } finally { setSaving(false); }
  };

  const startWalkInSession = async (input: { guestCount: number; customer: string; phone: string; note: string }) => {
    if (!walkInTable) return;
    setSaving(true);
    try {
      const session = await startWalkIn({ tableId: walkInTable.id, ...input });
      setWalkInTable(null);
      if (openMenuOnSelect) setOpenSession(session);
      push(`Đã mở ${walkInTable.number} và tạo hoá đơn ${session.orderCode ?? ""}.`.trim());
      await loadBranchData(true);
    } catch (error) {
      push(error instanceof Error ? error.message : "Không thể mở bàn này.", "err");
      await loadBranchData(true);
    } finally { setSaving(false); }
  };

  /** Check-in (nếu chưa) → xếp bàn → backend tạo phiên + hoá đơn → mở màn gọi món. */
  const seatReservation = async () => {
    if (!seating || !seatTarget) return;
    setSaving(true);
    try {
      if (seating.status === "confirmed") await checkInReservation(seating.id, seating.version);
      const session = await startReservationSession(seating.id, seatTarget.id);
      push(`Đã check-in ${seating.customer || "khách"} và mở hoá đơn tại ${seatTarget.number}.`);
      setSeatTarget(null);
      setSeating(null);
      setOpenSession(session);
      await loadBranchData(true);
    } catch (error) {
      push(error instanceof Error ? error.message : "Không thể xếp bàn cho khách này.", "err");
      setSeatTarget(null);
      await loadBranchData(true);
    } finally { setSaving(false); }
  };

  /** Khách đã tới nhưng chưa có bàn phù hợp: ghi nhận check-in để khách chờ. */
  const checkInOnly = async (res: AdminReservation) => {
    setSaving(true);
    try {
      await checkInReservation(res.id, res.version);
      push(`Đã check-in ${res.customer || "khách"}. Xếp bàn khi có bàn trống.`);
      setSeating(null);
      await loadBranchData(true);
    } catch (error) {
      push(error instanceof Error ? error.message : "Không thể check-in khách.", "err");
      await loadBranchData(true);
    } finally { setSaving(false); }
  };

  const archiveTable = async (table: AdminTable) => {
    if (!window.confirm(`Lưu trữ bàn ${table.number}? Bàn sẽ được ẩn khỏi sơ đồ nhưng lịch sử đặt chỗ vẫn còn.`)) return;
    try {
      await archiveTableManagementTable(table.id);
      push(`Đã lưu trữ bàn ${table.number}.`);
      await loadBranchData();
    } catch { push("Không thể lưu trữ bàn này.", "err"); }
  };

  const restoreTable = async (table: AdminTable) => {
    try {
      await restoreTableManagementTable(table.id);
      push(`Đã khôi phục bàn ${table.number}.`);
      await loadBranchData();
    } catch { push("Không thể khôi phục bàn này.", "err"); }
  };

  const saveRoom = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!editingRoom || editingRoom === "new" && !selectedBranchData) return;
    const form = new FormData(event.currentTarget);
    const room: AdminPrivateRoom = {
      id: editingRoom === "new" ? "" : editingRoom.id,
      branchId: editingRoom === "new" ? selectedBranchData!.id : editingRoom.branchId,
      name: String(form.get("name") ?? "").trim(),
      floor: String(form.get("floor") ?? "").trim(),
      capacity: Number(form.get("capacity") ?? 12),
      active: true,
    };
    if (!room.name || !Number.isInteger(room.capacity) || room.capacity < 1 || room.capacity > 12) return push("Tên phòng bắt buộc; sức chứa từ 1 đến 12 ghế.", "err");
    setSaving(true);
    try {
      if (editingRoom === "new") await createTableManagementRoom(room);
      else await updateTableManagementRoom({ ...editingRoom, ...room });
      setEditingRoom(null);
      push("Đã lưu phòng riêng.");
      await loadBranchData();
    } catch { push("Không thể lưu phòng riêng. Tên phòng có thể đã được dùng tại chi nhánh này.", "err"); }
    finally { setSaving(false); }
  };

  const archiveRoom = async (room: AdminPrivateRoom) => {
    if (!window.confirm(`Ngừng sử dụng phòng ${room.name}?`)) return;
    try {
      await archiveTableManagementRoom(room.id);
      push(`Đã ngừng sử dụng phòng ${room.name}.`);
      await loadBranchData();
    } catch { push("Không thể ngừng sử dụng phòng này.", "err"); }
  };

  const onTileClick = (table: AdminTable) => {
    if (mode === "configure") {
      if (table.archived) return;
      if (table.activeSession) return push(`${table.number} đang có phiên phục vụ, không sửa được lúc này.`, "err");
      return setEditingTable(table);
    }
    if (seating) return fitsSeating(table) ? setSeatTarget(table) : undefined;
    if (table.activeSession) return setOpenSession(table.activeSession);
    if (isFree(table) && canOperate) return setWalkInTable(table);
  };

  const renderTile = (table: AdminTable) => {
    const session = table.activeSession;
    const cleaning = isCleaning(table);
    const busy = !cleaning && isBusy(table);
    const maintenance = table.status === "maintenance";
    const fits = fitsSeating(table);
    const dimmed = !!seating && !fits;
    const elapsed = session?.status === "active" ? minutesSince(session.startedAt, now) : null;
    const clickable = mode === "configure" ? !table.archived : seating ? fits : !!session || (isFree(table) && canOperate);
    const statusText = table.archived ? "Đã lưu trữ" : maintenance ? "Bảo trì" : cleaning ? "Chờ dọn" : session ? "Đang phục vụ" : busy ? TABLE_META[table.status].label : "Trống";
    const tone = table.archived ? "text-slate-400 border border-dashed border-slate-300"
      : maintenance ? "text-slate-400"
      : cleaning ? "bg-amber-50 text-amber-800"
      : busy ? "bg-primary/10 text-primary"
      : "text-slate-600 hover:bg-slate-50";
    const caption = session?.status === "active"
      ? [elapsed !== null ? fmtDuration(elapsed) : null, session.orderTotal ? formatCurrency(session.orderTotal) : null].filter(Boolean).join("  ")
      : cleaning ? "Chờ dọn" : maintenance ? "Bảo trì" : fits ? (table.id === suggestedId ? "Gợi ý" : `${table.capacity} ghế`) : "";

    return (
      <div key={table.id} className={`relative transition-opacity ${dimmed ? "opacity-25" : ""}`}>
        <button
          type="button"
          disabled={!clickable}
          onClick={() => onTileClick(table)}
          title={session?.customer ? `${table.number}: ${session.customer}, ${session.guestCount} khách` : `${table.number}, ${table.capacity} ghế`}
          aria-label={`${table.number}, ${table.capacity} ghế, ${statusText}${session?.customer ? `, khách ${session.customer}` : ""}`}
          className={`flex h-[132px] w-full flex-col items-center justify-center gap-1.5 rounded-xl px-1 transition-colors ${tone} ${clickable ? "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary" : "cursor-default"} ${fits ? "bg-emerald-50 text-emerald-800 ring-2 ring-emerald-500" : ""}`}
        >
          <span className="relative flex h-[58px] items-center">
            <TableGlyph seats={table.capacity} room={!!table.roomId} />
            {(session?.reservationId || cleaning || maintenance || (fits && table.id === suggestedId)) && (
              <span className={`absolute -top-2 left-1/2 flex h-5 w-5 -translate-x-1/2 items-center justify-center rounded-full text-white ring-2 ring-white ${fits ? "bg-emerald-600" : cleaning ? "bg-amber-500" : maintenance ? "bg-slate-400" : "bg-secondary"}`} aria-hidden>
                {fits ? <Sparkles size={11} /> : cleaning ? <Brush size={11} /> : maintenance ? <Wrench size={11} /> : <CalendarCheck size={11} />}
              </span>
            )}
          </span>
          <span className={`max-w-full truncate text-sm ${busy || fits ? "font-semibold" : "font-medium"}`}>{table.number}</span>
          <span className="h-4 max-w-full truncate text-[11px] tabular-nums opacity-80">{caption}</span>
        </button>
        {mode === "configure" && canConfigure && !session && (
          <div className="absolute right-1 top-1 flex gap-0.5">
            {table.archived
              ? <button className="rounded-md bg-white p-1.5 text-slate-500 shadow-sm ring-1 ring-slate-200 hover:text-emerald-700" title="Khôi phục bàn" aria-label={`Khôi phục ${table.number}`} onClick={() => void restoreTable(table)}><RotateCcw size={13} /></button>
              : <button className="rounded-md bg-white p-1.5 text-slate-500 shadow-sm ring-1 ring-slate-200 hover:text-rose-700" title="Lưu trữ bàn" aria-label={`Lưu trữ ${table.number}`} onClick={() => void archiveTable(table)}><Archive size={13} /></button>}
          </div>
        )}
      </div>
    );
  };

  const showArrivals = mode === "operate" && canOperate && (arrivals.length > 0 || pendingToday > 0 || !!seating);

  return (
    <div className="space-y-5">
      <PageHeader
        title="Sơ đồ bàn"
        subtitle={`${!(isAdmin || branches.length > 1) && selectedBranchData ? `${selectedBranchData.name}. ` : ""}${mode === "operate" ? "Bấm bàn trống để nhận khách mới, bấm bàn đang phục vụ để gọi món và thanh toán." : "Thêm, sửa, lưu trữ bàn và phòng riêng của chi nhánh."}`}
        actions={<div className="flex flex-wrap items-center gap-2">
          {canConfigure && <div className="inline-flex rounded-lg border border-slate-200 bg-white p-0.5" role="tablist" aria-label="Chế độ sơ đồ">
            {([["operate", "Vận hành"], ["configure", "Cấu hình"]] as const).map(([key, label]) => <button key={key} role="tab" aria-selected={mode === key} onClick={() => switchMode(key)} className={`rounded-md px-3 py-1.5 text-sm font-medium ${mode === key ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"}`}>{key === "configure" && <Settings2 size={14} className="mr-1 inline" />}{label}</button>)}
          </div>}
          <button onClick={() => void loadBranchData()} className="btn btn-outline py-2! px-3! text-sm!" aria-label="Làm mới sơ đồ bàn"><RefreshCw size={15} />Làm mới</button>
        </div>}
      />

      {(isAdmin || branches.length > 1) && <section className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 lg:flex-row lg:items-center">
        {(isAdmin || branches.length > 1) ? <label className="relative block w-full lg:max-w-sm">
          <span className="sr-only">Chi nhánh</span>
          <Building2 size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <select value={selectedBranch} onChange={(e) => { setSelectedBranch(e.target.value); setSeating(null); }} className={`${inputCls} pl-9! pr-8!`} aria-label="Chi nhánh">
            {isAdmin && <option value="all">Tất cả chi nhánh</option>}
            {branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}
          </select>
          <ChevronDown size={15} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-500" />
        </label> : null}
      </section>}

      {mode === "configure" && <section className="flex flex-wrap items-center gap-2 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-3">
        <span className="mr-auto text-sm text-slate-600">{selectedBranch === "all" ? "Chọn một chi nhánh để thêm bàn hoặc phòng riêng." : "Bấm vào bàn để sửa tên, khu vực, sức chứa hoặc chuyển sang bảo trì."}</span>
        <button onClick={() => setIncludeArchived((v) => !v)} className="btn btn-outline py-2! px-3! text-sm!">{includeArchived ? "Ẩn bàn lưu trữ" : "Xem bàn lưu trữ"}</button>
        <button disabled={selectedBranch === "all" || !selectedBranch} onClick={() => setEditingRoom("new")} className="btn btn-outline py-2! px-3! text-sm! disabled:opacity-40"><DoorOpen size={15} />Tạo phòng riêng</button>
        <button disabled={selectedBranch === "all" || !selectedBranch} onClick={() => setEditingTable("new")} className="btn btn-primary py-2! px-3! text-sm! disabled:opacity-40"><Plus size={15} />Thêm bàn</button>
      </section>}

      {loadError && <div className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800"><CircleAlert size={17} />{loadError}</div>}

      <div className={`grid gap-5 ${showArrivals ? "xl:grid-cols-[300px_minmax(0,1fr)]" : ""}`}>
        {showArrivals && <aside className="space-y-3 xl:sticky xl:top-4 xl:self-start">
          <div className="rounded-2xl border border-slate-200 bg-white">
            <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-3"><CalendarClock size={16} className="text-slate-500" /><h2 className="font-semibold text-slate-900">Khách đặt bàn hôm nay</h2><span className="ml-auto rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">{arrivals.length}</span></div>
            <div className="max-h-[calc(100vh-16rem)] divide-y divide-slate-100 overflow-y-auto">
              {arrivals.length === 0 ? <p className="px-4 py-8 text-center text-sm text-slate-500">Không còn khách đặt bàn nào cần check-in hôm nay.</p> : arrivals.map((r) => {
                const late = lateMinutes(r.time, now);
                const active = seating?.id === r.id;
                return <article key={r.id} className={`px-4 py-3 ${active ? "bg-emerald-50" : ""}`}>
                  <div className="flex items-start gap-3">
                    <div className="w-12 shrink-0"><div className="text-base font-semibold tabular-nums text-slate-900">{r.time}</div>{r.status === "confirmed" && late > 15 && <div className="text-[11px] font-medium text-rose-700">Trễ {fmtDuration(late)}</div>}</div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate font-medium text-slate-900">{r.customer || "Khách"}</div>
                      <div className="text-xs text-slate-500">{r.partySize} khách{r.phone ? ` · ${r.phone}` : ""}</div>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {r.status === "seated" && <Badge tone="ok">Đã check-in · chờ bàn</Badge>}
                        {r.depositAmount > 0 && r.depositStatus === "success" && <Badge tone="info">Đã cọc {formatCurrency(r.depositAmount)}</Badge>}
                        {r.foodItems.length > 0 && <Badge tone="warn">{r.foodItems.reduce((n, i) => n + i.qty, 0)} món đặt trước</Badge>}
                        {selectedBranch === "all" && <Badge tone="neutral">{branchName(r.branchId)}</Badge>}
                      </div>
                      {r.note && <p className="mt-1 line-clamp-2 text-xs text-slate-500">“{r.note}”</p>}
                    </div>
                  </div>
                  <button onClick={() => setSeating(active ? null : r)} disabled={saving} className={`mt-2 w-full rounded-lg px-3 py-2 text-sm font-semibold ${active ? "border border-slate-300 bg-white text-slate-700" : "bg-emerald-700 text-white hover:bg-emerald-800"}`}>
                    {active ? "Huỷ chọn bàn" : r.status === "seated" ? "Xếp bàn" : "Check-in & xếp bàn"}
                  </button>
                </article>;
              })}
            </div>
            {pendingToday > 0 && <p className="border-t border-slate-100 px-4 py-2.5 text-xs text-amber-800">{pendingToday} đặt bàn hôm nay chưa được xác nhận — xác nhận trong trang Đặt bàn để check-in.</p>}
          </div>
        </aside>}

        <div className="min-w-0 space-y-4">
          {seating && <div className="flex flex-wrap items-center gap-3 rounded-xl border border-emerald-300 bg-emerald-50 px-4 py-3 text-sm text-emerald-900" role="status">
            <span className="flex-1">Chọn bàn cho <b>{seating.customer || "khách"}</b> · {seating.partySize} khách. {seatingFits.length ? `${seatingFits.length} bàn trống đủ chỗ đang được đánh dấu.` : "Hiện không có bàn trống đủ chỗ."}</span>
            {!seatingFits.length && seating.status === "confirmed" && <button disabled={saving} onClick={() => void checkInOnly(seating)} className="rounded-lg bg-emerald-700 px-3 py-1.5 font-semibold text-white">Chỉ check-in, xếp bàn sau</button>}
            <button onClick={() => setSeating(null)} className="inline-flex items-center gap-1 rounded-lg px-2 py-1.5 font-medium hover:bg-emerald-100"><X size={15} />Huỷ</button>
          </div>}


          {isAdmin && selectedBranch === "all" && !loading && !seating && <section className="grid gap-3 md:grid-cols-3">
            {branches.map((branch) => {
              const list = tables.filter((t) => t.branchId === branch.id && !t.archived);
              return <button key={branch.id} onClick={() => setSelectedBranch(branch.id)} className="rounded-xl border border-slate-200 bg-white p-3 text-left hover:border-emerald-400">
                <span className="block truncate font-medium text-slate-900">{branch.name}</span>
                <span className="mt-1 block text-xs text-slate-600">{list.filter(isFree).length}/{list.length} bàn trống · {list.filter((t) => isBusy(t) && !isCleaning(t)).length} đang phục vụ</span>
              </button>;
            })}
          </section>}

          <section className="rounded-2xl border border-slate-200 bg-white">
            <div className="flex flex-col gap-3 border-b border-slate-100 px-3 pt-3 sm:flex-row sm:items-end">
              <nav className="-mb-px flex min-w-0 flex-1 gap-1 overflow-x-auto" aria-label="Khu vực">
                {[ALL_AREAS, ...areas].map((area) => <button key={area} onClick={() => setAreaFilter(area)} aria-pressed={areaFilter === area} className={`shrink-0 rounded-t-lg border-b-2 px-3.5 pb-2.5 pt-2 text-sm font-medium transition-colors ${areaFilter === area ? "border-primary text-primary" : "border-transparent text-slate-500 hover:text-slate-900"}`}>{area}</button>)}
              </nav>
              <label className="relative mb-2 block w-full sm:w-56"><Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Tìm bàn, tên khách" aria-label="Tìm bàn" className={`${inputCls} py-2! pl-9!`} /></label>
            </div>
            <fieldset className="flex flex-wrap items-center gap-x-5 gap-y-2 px-4 py-3 text-sm">
              <legend className="sr-only">Lọc theo trạng thái</legend>
              {([["all", "Tất cả", counts.all], ["busy", "Đang dùng", counts.busy], ["available", "Còn trống", counts.available]] as const).map(([key, label, n]) => (
                <label key={key} className="inline-flex cursor-pointer items-center gap-2 text-slate-700">
                  <input type="radio" name="table-status" checked={statusFilter === key} onChange={() => setStatusFilter(key)} className="h-4 w-4 accent-[var(--color-primary)]" />
                  {label} <span className="tabular-nums text-slate-400">({n})</span>
                </label>
              ))}
              <span className="ml-auto hidden text-xs text-slate-500 sm:inline">{guestsSeated} khách đang ngồi</span>
            </fieldset>

            {loading ? <div className="grid grid-cols-3 gap-2 px-3 pb-4 sm:grid-cols-4 md:grid-cols-6 xl:grid-cols-8">{Array.from({ length: 16 }).map((_, i) => <div key={i} className="h-[118px] animate-pulse rounded-xl bg-slate-100" />)}</div>
              : visibleTables.length === 0 ? <div className="px-6 pb-12 pt-8 text-center"><h3 className="font-semibold text-slate-800">Không có bàn phù hợp</h3><p className="mt-1 text-sm text-slate-500">{tables.length ? "Thử đổi khu vực, trạng thái hoặc từ khoá tìm kiếm." : canConfigure ? "Chuyển sang chế độ Cấu hình để thêm bàn." : "Chi nhánh chưa có bàn."}</p></div>
              : <div className="space-y-5 px-3 pb-4">
                {tablesByBranch.map(([branchId, list]) => <div key={branchId}>
                  {selectedBranch === "all" && <h2 className="mb-2 px-1 text-sm font-semibold text-slate-700">{branchName(branchId)}</h2>}
                  <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-6 xl:grid-cols-8">{list.map(renderTile)}</div>
                </div>)}
              </div>}

            {mode === "operate" && canOperate && <label className="flex cursor-pointer items-center gap-2 border-t border-slate-100 px-4 py-3 text-sm text-slate-700">
              <input type="checkbox" checked={openMenuOnSelect} onChange={(e) => toggleOpenMenu(e.target.checked)} className="h-4 w-4 accent-[var(--color-primary)]" />
              Mở thực đơn ngay sau khi nhận khách
            </label>}
          </section>

          {mode === "configure" && selectedBranch !== "all" && rooms.length > 0 && <section className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4">
            <div><h2 className="font-semibold text-slate-900">Phòng riêng</h2><p className="text-sm text-slate-500">Tên phòng, tầng và sức chứa tối đa.</p></div>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{rooms.map((room) => <article key={room.id} className={`flex items-center justify-between gap-3 rounded-xl border p-3 ${room.active ? "border-slate-200" : "border-slate-200 bg-slate-50 opacity-70"}`}>
              <div><div className="font-medium text-slate-900">{room.name}{!room.active && <span className="ml-2 text-xs text-slate-500">Đã ngừng</span>}</div><div className="text-xs text-slate-500">{room.floor || "Chưa ghi tầng"} · tối đa {room.capacity} ghế</div></div>
              <div className="flex gap-1"><button aria-label={`Sửa phòng ${room.name}`} onClick={() => setEditingRoom(room)} className="rounded p-2 text-slate-500 hover:bg-slate-100"><Pencil size={15} /></button>{room.active ? <button aria-label={`Ngừng sử dụng phòng ${room.name}`} onClick={() => void archiveRoom(room)} className="rounded p-2 text-slate-500 hover:bg-rose-50 hover:text-rose-700"><Archive size={15} /></button> : <button aria-label={`Kích hoạt phòng ${room.name}`} onClick={() => void updateTableManagementRoom({ ...room, active: true }).then(() => loadBranchData())} className="rounded p-2 text-slate-500 hover:bg-emerald-50 hover:text-emerald-700"><RotateCcw size={15} /></button>}</div>
            </article>)}</div>
          </section>}
        </div>
      </div>

      <RecordDrawer<AdminTable> open={editingTable !== null} title={editingTable === "new" ? "Thêm bàn vào chi nhánh" : "Sửa thông tin bàn"} fields={fields} initial={tableInitial} saving={saving} onClose={() => setEditingTable(null)} onSave={saveTable} />

      {walkInTable && <WalkInDialog table={walkInTable} saving={saving} onCancel={() => setWalkInTable(null)} onSubmit={(input) => void startWalkInSession(input)} />}

      <ConfirmModal
        open={!!seatTarget && !!seating}
        busy={saving}
        title={`Xếp ${seating?.customer || "khách"} vào ${seatTarget?.number ?? ""}?`}
        message={`${seating?.partySize ?? 0} khách · bàn ${seatTarget?.capacity ?? 0} ghế. Hệ thống sẽ ${seating?.status === "confirmed" ? "check-in, " : ""}xếp bàn và tạo hoá đơn${seating?.foodItems.length ? " kèm các món đặt trước" : ""}, rồi mở màn gọi món.`}
        confirmLabel={saving ? "Đang xếp bàn…" : "Xếp bàn & mở hoá đơn"}
        onConfirm={() => void seatReservation()}
        onCancel={() => setSeatTarget(null)}
      />

      <DiningSessionDrawer session={openSession} tables={tables} onClose={() => setOpenSession(null)} onChanged={() => void loadBranchData(true)} />

      {editingRoom && <div className="fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/40 p-4" role="presentation" onMouseDown={(e) => { if (e.target === e.currentTarget) setEditingRoom(null); }}>
        <form onSubmit={saveRoom} className="w-full max-w-md space-y-4 rounded-2xl bg-white p-5 shadow-xl" aria-label="Thông tin phòng riêng">
          <div><h2 className="text-lg font-semibold">{editingRoom === "new" ? "Tạo phòng riêng" : "Sửa phòng riêng"}</h2><p className="mt-1 text-sm text-slate-500">Phòng thuộc chi nhánh {selectedBranchData?.name ?? "đang chọn"}.</p></div>
          <label className="block text-sm font-medium">Tên phòng<input name="name" required maxLength={80} defaultValue={editingRoom === "new" ? "" : editingRoom.name} className={`${inputCls} mt-1`} placeholder="Ví dụ: Phòng VIP 1" /></label>
          <label className="block text-sm font-medium">Tầng<input name="floor" maxLength={50} defaultValue={editingRoom === "new" ? "" : editingRoom.floor} className={`${inputCls} mt-1`} placeholder="Ví dụ: Tầng 2" /></label>
          <label className="block text-sm font-medium">Sức chứa tối đa<input name="capacity" type="number" min={1} max={12} defaultValue={editingRoom === "new" ? 12 : editingRoom.capacity} className={`${inputCls} mt-1`} /></label>
          <div className="flex justify-end gap-2 pt-2"><button type="button" onClick={() => setEditingRoom(null)} className="btn btn-outline py-2! px-4!">Hủy</button><button disabled={saving} className="btn btn-primary py-2! px-4!">{saving ? "Đang lưu..." : "Lưu phòng"}</button></div>
        </form>
      </div>}
    </div>
  );
}

function Badge({ tone, children }: { tone: "ok" | "info" | "warn" | "neutral"; children: React.ReactNode }) {
  const cls = { ok: "bg-emerald-100 text-emerald-800", info: "bg-sky-100 text-sky-800", warn: "bg-amber-100 text-amber-900", neutral: "bg-slate-100 text-slate-700" }[tone];
  return <span className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${cls}`}>{children}</span>;
}

/** Nhận khách vãng lai: chọn nhanh số khách, thông tin liên hệ không bắt buộc. */
function WalkInDialog({ table, saving, onCancel, onSubmit }: { table: AdminTable; saving: boolean; onCancel: () => void; onSubmit: (input: { guestCount: number; customer: string; phone: string; note: string }) => void }) {
  const max = Math.min(12, table.capacity);
  const [guests, setGuests] = useState(Math.min(2, max));
  const [customer, setCustomer] = useState("");
  const [phone, setPhone] = useState("");
  const [note, setNote] = useState("");
  const [more, setMore] = useState(false);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onCancel();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onCancel]);

  return (
    <div className="fixed inset-0 z-[70] flex items-end justify-center bg-slate-950/40 p-4 sm:items-center" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onCancel(); }}>
      <form onSubmit={(e) => { e.preventDefault(); onSubmit({ guestCount: guests, customer: customer.trim(), phone: phone.trim(), note: note.trim() }); }} className="w-full max-w-sm space-y-5 rounded-2xl bg-white p-5 shadow-xl" aria-label={`Nhận khách tại ${table.number}`}>
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Nhận khách · {table.number}</h2>
          <p className="mt-0.5 text-sm text-slate-500">{table.roomName ? `Phòng ${table.roomName}` : table.zone} · tối đa {max} khách</p>
        </div>
        <div>
          <div className="mb-2 text-sm font-medium text-slate-700">Số khách</div>
          <div className="flex items-center gap-3">
            <button type="button" onClick={() => setGuests((g) => Math.max(1, g - 1))} disabled={guests <= 1} aria-label="Bớt một khách" className="flex h-11 w-11 items-center justify-center rounded-full border border-slate-200 text-slate-700 hover:bg-slate-50 disabled:opacity-40"><Minus size={18} /></button>
            <output className="w-12 text-center text-3xl font-semibold tabular-nums text-slate-900" aria-live="polite">{guests}</output>
            <button type="button" onClick={() => setGuests((g) => Math.min(max, g + 1))} disabled={guests >= max} aria-label="Thêm một khách" className="flex h-11 w-11 items-center justify-center rounded-full border border-slate-200 text-slate-700 hover:bg-slate-50 disabled:opacity-40"><Plus size={18} /></button>
          </div>
          {max > 1 && <div className="mt-3 flex flex-wrap gap-1.5">{Array.from({ length: max }, (_, i) => i + 1).map((n) => <button type="button" key={n} onClick={() => setGuests(n)} className={`h-8 min-w-8 rounded-md px-2 text-sm ${guests === n ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"}`}>{n}</button>)}</div>}
        </div>
        {more ? <div className="space-y-3">
          <label className="block text-sm font-medium text-slate-700">Tên khách<input value={customer} onChange={(e) => setCustomer(e.target.value)} maxLength={150} className={`${inputCls} mt-1`} placeholder="Không bắt buộc" /></label>
          <label className="block text-sm font-medium text-slate-700">Số điện thoại<input value={phone} onChange={(e) => setPhone(e.target.value)} maxLength={20} inputMode="tel" className={`${inputCls} mt-1`} placeholder="Không bắt buộc" /></label>
          <label className="block text-sm font-medium text-slate-700">Ghi chú<textarea value={note} onChange={(e) => setNote(e.target.value)} className={`${inputCls} mt-1 min-h-16`} placeholder="Có trẻ em, cần ghế em bé…" /></label>
        </div> : <button type="button" onClick={() => setMore(true)} className="text-sm font-medium text-emerald-800 hover:underline">+ Thêm tên, số điện thoại, ghi chú</button>}
        <div className="flex gap-2 pt-1">
          <button type="button" onClick={onCancel} className="btn btn-outline flex-1 py-2.5!">Huỷ</button>
          <button disabled={saving} className="btn btn-primary flex-[2] py-2.5!">{saving ? "Đang mở bàn…" : "Mở bàn & tạo hoá đơn"}</button>
        </div>
      </form>
    </div>
  );
}

/** Hình bàn nhìn từ trên xuống: số ghế mỗi cạnh dài theo sức chứa, phòng riêng có khung bao. */
function TableGlyph({ seats, room }: { seats: number; room: boolean }) {
  const perSide = Math.min(3, Math.max(1, Math.ceil((seats - (seats > 4 ? 2 : 0)) / 2)));
  const ends = seats > 4;
  const w = 44 + (perSide - 1) * 14;
  const W = w + (ends ? 22 : 10);
  const x0 = (W - w) / 2;
  const chairs = Array.from({ length: perSide }, (_, i) => x0 + (w * (i + 0.5)) / perSide - 5);
  return (
    <svg width={Math.min(Math.round(W * 1.3), 92)} viewBox={`0 0 ${W} 44`} fill="none" aria-hidden className="block h-auto">
      {room && <rect x="0.75" y="0.75" width={W - 1.5} height="42.5" rx="9" stroke="currentColor" strokeOpacity=".35" strokeDasharray="3 3" />}
      {chairs.map((x, i) => <rect key={`t${i}`} x={x} y="4" width="10" height="4" rx="2" fill="currentColor" fillOpacity=".5" />)}
      {chairs.map((x, i) => <rect key={`b${i}`} x={x} y="36" width="10" height="4" rx="2" fill="currentColor" fillOpacity=".5" />)}
      {ends && <><rect x={x0 - 7} y="17" width="4" height="10" rx="2" fill="currentColor" fillOpacity=".5" /><rect x={x0 + w + 3} y="17" width="4" height="10" rx="2" fill="currentColor" fillOpacity=".5" /></>}
      <rect x={x0} y="10.5" width={w} height="23" rx="6" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}
