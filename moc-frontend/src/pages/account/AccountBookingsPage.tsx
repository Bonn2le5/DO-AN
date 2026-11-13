import { useState } from "react";
import { Link } from "react-router-dom";
import { CalendarDays, ChevronDown, Clock, MapPin, Users } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { huyDatBanCuaToi, layDatBanCuaToi, taoPhienThanhToanPayOS } from "@/api/reservations.api";
import { cn, formatCurrency, formatDate } from "@/lib/utils";
import type { ThongTinDatBan } from "@/types";

const STATUS: Record<string, { label: string; cls: string }> = {
  cho_xac_nhan: { label: "Chờ xác nhận", cls: "bg-amber-100 text-amber-800" },
  cho_thanh_toan: { label: "Chờ đặt cọc", cls: "bg-amber-100 text-amber-800" },
  da_xac_nhan: { label: "Đã xác nhận", cls: "bg-sky-100 text-sky-800" },
  khach_da_den: { label: "Đang dùng bữa", cls: "bg-emerald-100 text-emerald-800" },
  hoan_tat: { label: "Hoàn tất", cls: "bg-black/5 text-dark" },
  da_huy: { label: "Đã hủy", cls: "bg-red-100 text-red-700" },
  khach_khong_den: { label: "Không đến", cls: "bg-red-100 text-red-700" },
};

const DEPOSIT: Record<string, string> = {
  chua_thanh_toan: "Chưa cọc",
  dang_xu_ly: "Đang xử lý",
  thanh_cong: "Đã cọc",
  that_bai: "Thanh toán lỗi",
  da_hoan_tien: "Đã hoàn cọc",
  hoan_tien_mot_phan: "Hoàn một phần",
};

const HINH_THUC: Record<string, string> = {
  chi_giu_cho: "Chỉ giữ chỗ",
  dat_ban_va_goi_mon: "Đặt bàn + gọi món",
  dat_ban_goi_mon_chinh_sua: "Đặt bàn + gọi món (chỉnh sửa)",
};

// Khớp TRANG_THAI_DUOC_HUY ở backend: sau khi nhân viên check-in (đang dùng bữa) thì không huỷ được nữa.
const DUOC_HUY = new Set(["cho_xac_nhan", "cho_thanh_toan", "da_xac_nhan"]);

const canPayDeposit = (r: ThongTinDatBan) =>
  r.soTienCoc > 0 &&
  r.trangThaiThanhToanCoc === "chua_thanh_toan" &&
  (r.trangThai === "cho_thanh_toan" || r.trangThai === "cho_xac_nhan");

const formatDateTime = (v?: string) =>
  v ? new Intl.DateTimeFormat("vi-VN", { dateStyle: "short", timeStyle: "short" }).format(new Date(v)) : "";

const apiError = (e: any, fallback: string) => {
  const d = e?.response?.data;
  const msg = d?.chi_tiet ?? d?.detail ?? d?.dat_ban_id ?? d?.non_field_errors;
  return (Array.isArray(msg) ? msg[0] : msg) || fallback;
};

export default function AccountBookingsPage() {
  const { data, loading, error, refetch } = useAsync(layDatBanCuaToi);

  return (
    <div>
      <h2 className="font-display text-xl mb-6">Lịch sử đặt bàn</h2>
      {loading ? (
        <div className="space-y-3">
          {[0, 1].map((i) => <div key={i} className="card h-28 animate-pulse bg-black/5" />)}
        </div>
      ) : error ? (
        <div className="card p-10 text-center text-sm text-muted">Không tải được lịch sử đặt bàn.</div>
      ) : !data?.length ? (
        <div className="card p-10 text-center">
          <CalendarDays width={30} height={30} className="mx-auto mb-3 text-muted" />
          <p className="text-muted text-sm mb-4">Bạn chưa có lần đặt bàn nào.</p>
          <Link to="/dat-ban" className="btn btn-primary">Đặt bàn ngay</Link>
        </div>
      ) : (
        <ul className="space-y-3">
          {data.map((r) => <BookingCard key={r.id} r={r} onChanged={() => refetch(true)} />)}
        </ul>
      )}
    </div>
  );
}

function BookingCard({ r, onChanged }: { r: ThongTinDatBan; onChanged: () => void }) {
  const [open, setOpen] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [lyDo, setLyDo] = useState("");
  const [busy, setBusy] = useState<"" | "huy" | "coc">("");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const st = STATUS[r.trangThai] ?? { label: r.trangThai, cls: "bg-black/5 text-dark" };
  const daHuy = r.trangThai === "da_huy" || r.trangThai === "khach_khong_den";
  const daCoc = r.trangThaiThanhToanCoc === "thanh_cong";

  const huy = async () => {
    setBusy("huy");
    setMsg(null);
    try {
      const kq = await huyDatBanCuaToi(r.id, lyDo.trim());
      setConfirming(false);
      setMsg({
        ok: true,
        text: kq.soTienHoan > 0
          ? `Đã huỷ. Nhà hàng sẽ hoàn ${formatCurrency(kq.soTienHoan)} (${kq.phanTramHoan}% tiền cọc).`
          : daCoc ? "Đã huỷ. Theo chính sách, lần huỷ này không được hoàn cọc." : "Đã huỷ đặt bàn.",
      });
      onChanged();
    } catch (e) {
      setMsg({ ok: false, text: apiError(e, "Không huỷ được, vui lòng thử lại.") });
      onChanged(); // trạng thái có thể đã đổi (vd. vừa check-in) → tải lại để ẩn nút
    } finally {
      setBusy("");
    }
  };

  const thanhToan = async () => {
    setBusy("coc");
    setMsg(null);
    try {
      const phien = await taoPhienThanhToanPayOS(r.id);
      if (!phien.duongDanThanhToan) throw new Error();
      window.location.href = phien.duongDanThanhToan;
    } catch (e) {
      setMsg({ ok: false, text: apiError(e, "Không tạo được phiên thanh toán, vui lòng thử lại.") });
      setBusy("");
      onChanged();
    }
  };

  return (
    <li className="card p-5">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <span className="font-semibold text-sm">{r.maDatBan ? `#${r.maDatBan}` : `Đặt bàn #${r.id}`}</span>
        <span className={cn("px-2.5 py-1 rounded-full text-xs font-semibold", st.cls)}>{st.label}</span>
      </div>
      <div className="grid sm:grid-cols-2 gap-x-6 gap-y-2 text-sm text-muted">
        <span className="flex items-center gap-2"><CalendarDays width={15} height={15} />{r.ngayDat ? formatDate(r.ngayDat) : "—"}</span>
        <span className="flex items-center gap-2"><Clock width={15} height={15} />{r.gioDat.slice(0, 5) || "—"}</span>
        <span className="flex items-center gap-2"><MapPin width={15} height={15} />{r.tenChiNhanh || "—"}{r.tenBanAn ? ` · Bàn ${r.tenBanAn}` : ""}</span>
        <span className="flex items-center gap-2"><Users width={15} height={15} />{r.soLuongKhach} khách</span>
      </div>

      {r.soTienCoc > 0 && (
        <div className="mt-3 pt-3 border-t border-black/5 flex justify-between text-sm">
          <span className="text-muted">Tiền cọc · {
            // Phiếu đã huỷ nhưng cọc còn "thành công": nhà hàng chưa chuyển khoản hoàn.
            daHuy && daCoc ? "Chờ nhà hàng hoàn cọc" : DEPOSIT[r.trangThaiThanhToanCoc] ?? r.trangThaiThanhToanCoc
          }</span>
          <span className="font-semibold">{formatCurrency(r.soTienCoc)}</span>
        </div>
      )}

      {open && <BookingDetail r={r} />}

      {confirming && (
        <div className="mt-3 rounded-lg bg-red-50 p-4 text-sm">
          <p className="font-semibold text-red-800 mb-1">Huỷ đặt bàn này?</p>
          {daCoc && (
            <p className="text-red-700 mb-2">Tiền cọc được hoàn theo chính sách huỷ, tuỳ thời điểm bạn huỷ so với giờ hẹn.</p>
          )}
          <textarea
            value={lyDo}
            onChange={(e) => setLyDo(e.target.value)}
            maxLength={300}
            rows={2}
            placeholder="Lý do huỷ (không bắt buộc)"
            className="w-full rounded-md border border-black/10 bg-white p-2 mb-3"
          />
          <div className="flex gap-2">
            <button type="button" className="btn bg-red-600 text-white hover:bg-red-700 disabled:opacity-60" disabled={busy !== ""} onClick={huy}>
              {busy === "huy" ? "Đang huỷ…" : "Xác nhận huỷ"}
            </button>
            <button type="button" className="btn btn-outline" disabled={busy !== ""} onClick={() => setConfirming(false)}>Giữ lại</button>
          </div>
        </div>
      )}

      {msg && (
        <p className={cn("mt-3 text-sm", msg.ok ? "text-emerald-700" : "text-red-700")}>{msg.text}</p>
      )}

      <div className="mt-3 pt-3 border-t border-black/5 flex flex-wrap items-center gap-2">
        <button type="button" className="text-sm text-muted inline-flex items-center gap-1 mr-auto" onClick={() => setOpen((o) => !o)}>
          {open ? "Thu gọn" : "Xem chi tiết"}
          <ChevronDown width={15} height={15} className={cn("transition-transform", open && "rotate-180")} />
        </button>
        {canPayDeposit(r) && (
          <button type="button" className="btn btn-primary" disabled={busy !== ""} onClick={thanhToan}>
            {busy === "coc" ? "Đang mở thanh toán…" : `Thanh toán cọc ${formatCurrency(r.soTienCoc)}`}
          </button>
        )}
        {DUOC_HUY.has(r.trangThai) && !confirming && (
          <button type="button" className="btn text-red-700" disabled={busy !== ""} onClick={() => { setMsg(null); setConfirming(true); }}>
            Huỷ đặt bàn
          </button>
        )}
      </div>
    </li>
  );
}

function BookingDetail({ r }: { r: ThongTinDatBan }) {
  return (
    <dl className="mt-3 pt-3 border-t border-black/5 grid gap-3 text-sm">
      {r.hinhThuc && (
        <div className="flex justify-between gap-4">
          <dt className="text-muted">Hình thức</dt>
          <dd>{HINH_THUC[r.hinhThuc] ?? r.hinhThuc}</dd>
        </div>
      )}
      {(r.tenKhachHang || r.soDienThoai) && (
        <div className="flex justify-between gap-4">
          <dt className="text-muted">Người nhận bàn</dt>
          <dd className="text-right">
            {r.tenKhachHang}
            {r.soDienThoai && (
              <>
                {r.tenKhachHang && " · "}
                <a href={`tel:${r.soDienThoai}`} className="underline underline-offset-2">{r.soDienThoai}</a>
              </>
            )}
          </dd>
        </div>
      )}
      <div className="flex justify-between gap-4">
        <dt className="text-muted">Đặt lúc</dt>
        <dd>{formatDateTime(r.taoLuc)}</dd>
      </div>
      {r.danhSachMonAn.length > 0 && (
        <div>
          <dt className="text-muted mb-1">Món đặt trước</dt>
          <dd>
            <ul className="space-y-1">
              {r.danhSachMonAn.map((m, i) => {
                const gia = m.donGiaLucDat ?? m.monAn.donGia;
                return (
                  <li key={`${m.monAn.id}-${i}`} className="flex justify-between gap-4">
                    <span>{m.soLuong} × {m.monAn.tenMon}</span>
                    <span>{formatCurrency(gia * m.soLuong)}</span>
                  </li>
                );
              })}
              {r.tienMonAn > 0 && (
                <li className="flex justify-between gap-4 font-semibold pt-1">
                  <span>Tạm tính</span><span>{formatCurrency(r.tienMonAn)}</span>
                </li>
              )}
            </ul>
          </dd>
        </div>
      )}
      {r.ghiChu && (
        <div className="flex justify-between gap-4">
          <dt className="text-muted">Ghi chú</dt>
          <dd className="text-right whitespace-pre-line">{r.ghiChu}</dd>
        </div>
      )}
      {r.huyLuc && (
        <div className="flex justify-between gap-4">
          <dt className="text-muted">Huỷ lúc</dt>
          <dd className="text-right">{formatDateTime(r.huyLuc)}{r.lyDoHuy ? ` · ${r.lyDoHuy}` : ""}</dd>
        </div>
      )}
      {r.hoanCoc && (
        <div className="rounded-lg bg-black/5 p-3">
          <p className="font-semibold mb-1">
            {r.hoanCoc.soTien > 0
              ? `Đã hoàn ${formatCurrency(r.hoanCoc.soTien)} (${r.hoanCoc.phanTram}% tiền cọc)`
              : "Không được hoàn cọc theo chính sách huỷ"}
          </p>
          <p className="text-muted">
            {formatDateTime(r.hoanCoc.luc)}
            {r.hoanCoc.maGiaoDich ? ` · Mã giao dịch ${r.hoanCoc.maGiaoDich}` : ""}
          </p>
          {r.hoanCoc.ghiChu && <p className="text-muted mt-1">{r.hoanCoc.ghiChu}</p>}
        </div>
      )}
    </dl>
  );
}
