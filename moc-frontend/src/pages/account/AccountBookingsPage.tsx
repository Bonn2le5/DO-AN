import { Link } from "react-router-dom";
import { CalendarDays, Clock, MapPin, Users } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { layDatBanCuaToi } from "@/api/reservations.api";
import { cn, formatCurrency, formatDate } from "@/lib/utils";

const STATUS: Record<string, { label: string; cls: string }> = {
  cho_xac_nhan: { label: "Chờ xác nhận", cls: "bg-amber-100 text-amber-800" },
  cho_thanh_toan: { label: "Chờ đặt cọc", cls: "bg-amber-100 text-amber-800" },
  da_xac_nhan: { label: "Đã xác nhận", cls: "bg-sky-100 text-sky-800" },
  khach_da_den: { label: "Đã check-in", cls: "bg-emerald-100 text-emerald-800" },
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

export default function AccountBookingsPage() {
  const { data, loading, error } = useAsync(layDatBanCuaToi);

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
          {data.map((r) => {
            const st = STATUS[r.trangThai] ?? { label: r.trangThai, cls: "bg-black/5 text-dark" };
            return (
              <li key={r.id} className="card p-5">
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
                      (r.trangThai === "da_huy" || r.trangThai === "khach_khong_den") && r.trangThaiThanhToanCoc === "thanh_cong"
                        ? "Chờ nhà hàng hoàn cọc"
                        : DEPOSIT[r.trangThaiThanhToanCoc] ?? r.trangThaiThanhToanCoc
                    }</span>
                    <span className="font-semibold">{formatCurrency(r.soTienCoc)}</span>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
