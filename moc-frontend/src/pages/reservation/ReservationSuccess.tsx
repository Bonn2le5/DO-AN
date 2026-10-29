import { CheckCircle2, UtensilsCrossed } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import type { Reservation, ReservationFoodItem } from "@/types";

export default function ReservationSuccess({
  reservation,
  onReset,
}: {
  reservation: Reservation;
  onReset: () => void;
}) {
  const foodItems = reservation.foodItems ?? reservation.danhSachMonAn ?? [];
  const hasFood = foodItems.length > 0;
  const depositPaid = (reservation.depositAmount ?? reservation.soTienCoc ?? 0) > 0
    && ["success", "thanh_cong"].includes(reservation.depositStatus ?? reservation.trangThaiThanhToanCoc ?? "");

  return (
    <div className="max-w-lg mx-auto px-5 py-16 text-center">
      <div className="w-20 h-20 rounded-full bg-success/10 flex items-center justify-center mx-auto mb-6">
        <CheckCircle2 width={40} height={40} className="text-success" />
      </div>
      <h1 className="font-display text-3xl mb-2">{depositPaid ? "Đã nhận cọc và đặt chỗ" : "Đã gửi yêu cầu đặt chỗ"}</h1>
      <p className="text-muted mb-8">
        Nhà hàng sẽ gọi điện xác nhận thông tin với bạn. Hẹn gặp bạn tại MỘC!
      </p>

      <div className="card p-6 text-left space-y-4">
        <div className="flex items-center justify-between border-b border-black/8">
          <span className="font-display text-lg">#{reservation.id}</span>
          <span className="text-xs font-bold uppercase tracking-wide bg-success/10 text-success px-3 py-1 rounded-full">
            {reservation.status === "da_xac_nhan" || reservation.trangThai === "da_xac_nhan"
              ? "Nhà hàng đã xác nhận"
              : depositPaid ? "Đã nhận cọc · Chờ nhà hàng gọi" : "Chờ nhà hàng gọi xác nhận"}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <Row label="Bàn" value={reservation.tableLabel ?? reservation.tenBanAn ?? "Chưa xếp bàn"} />
          <Row
            label="Thời gian"
            value={`${reservation.time ?? reservation.gioDat} · ${reservation.date ?? reservation.ngayDat}`}
          />
          <Row label="Số khách" value={String(reservation.partySize ?? reservation.soLuongKhach ?? 2)} />
          <Row label="Người đặt" value={reservation.customerName ?? reservation.tenKhachHang ?? ""} />
        </div>

        {hasFood && (
          <div className="pt-4 border-t border-black/8">
            <div className="text-xs font-bold uppercase tracking-wide text-muted mb-2.5 flex items-center gap-1.5">
              <UtensilsCrossed width={13} height={13} /> Đơn món đã đặt trước
            </div>
            <div className="space-y-1.5">
              {foodItems.map((i: ReservationFoodItem) => (
                <div key={i.food.id} className="flex justify-between text-sm">
                  <span>
                    ✓ {i.quantity} × {i.food.name ?? i.food.tenMon}
                  </span>
                  <span className="text-muted">
                    {formatCurrency((i.food.price ?? i.food.donGia ?? 0) * i.quantity)}
                  </span>
                </div>
              ))}
            </div>
            <div className="flex justify-between text-sm font-semibold mt-2 pt-2 border-t border-black/6">
              <span>Tiền món</span>
              <span>{formatCurrency(reservation.foodSubtotal ?? reservation.tienMonAn ?? 0)}</span>
            </div>
          </div>
        )}

        {(reservation.depositAmount ?? reservation.soTienCoc ?? 0) > 0 && (
          <div className="flex justify-between items-center pt-4 border-t border-black/8">
            <span className="text-sm font-bold">Đã cọc</span>
            <span className="font-display text-xl text-primary">
              {formatCurrency(reservation.depositAmount ?? reservation.soTienCoc ?? 0)}
            </span>
          </div>
        )}
      </div>

      <button onClick={onReset} className="btn btn-outline mt-8">
        Đặt thêm bàn khác
      </button>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-muted text-xs">{label}</div>
      <div className="font-medium">{value}</div>
    </div>
  );
}
