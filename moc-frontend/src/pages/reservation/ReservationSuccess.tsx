import { CheckCircle2 } from "lucide-react";
import { Link } from "react-router-dom";
import { formatCurrency } from "@/lib/utils";
import type { ThongTinDatBan } from "@/types";
import ReservationTicket from "./ReservationTicket";

export default function ReservationSuccess({
  reservation,
  branchName = "",
  onReset,
}: {
  reservation: ThongTinDatBan;
  branchName?: string;
  onReset: () => void;
}) {
  const foodItems = reservation.danhSachMonAn ?? [];
  const deposit = reservation.soTienCoc ?? 0;
  const depositPaid = deposit > 0
    && ["success", "thanh_cong"].includes(reservation.trangThaiThanhToanCoc ?? "");
  const confirmed = reservation.trangThai === "da_xac_nhan";
  const statusText = confirmed
    ? "Nhà hàng đã xác nhận"
    : depositPaid ? "Đã nhận cọc, chờ nhà hàng gọi xác nhận" : "Chờ nhà hàng gọi xác nhận";

  return (
    <div className="reservation-ui max-w-xl mx-auto px-4 sm:px-5 py-12 sm:py-16">
      <div className="text-center mb-8">
        <CheckCircle2 width={44} height={44} className="text-success mx-auto mb-4" />
        <h1 className="font-display text-[30px] sm:text-[34px] leading-tight">
          {depositPaid ? "Đã nhận cọc, chỗ của bạn đã được giữ" : "Đã gửi yêu cầu đặt chỗ"}
        </h1>
        <p className="text-muted mt-2 max-w-[48ch] mx-auto">
          Nhà hàng sẽ gọi số {reservation.soDienThoai} để xác nhận. Hẹn gặp bạn tại MỘC.
        </p>
      </div>

      <ReservationTicket
        branchName={branchName}
        date={reservation.ngayDat ?? ""}
        time={reservation.gioDat ?? ""}
        partySize={reservation.soLuongKhach ?? 2}
        foodItems={foodItems}
        foodSubtotal={reservation.tienMonAn ?? 0}
        tableLabel={reservation.tenBanAn || reservation.tenBanAn}
        topLine={<>Mã đặt chỗ <strong className="text-text">#{reservation.id}</strong> · {statusText}</>}
      >
        {deposit > 0 && (
          <div className="flex items-baseline justify-between gap-3 mt-4 pt-3 border-t border-black/8">
            <span className="font-semibold">{depositPaid ? "Đã cọc" : "Tiền cọc"}</span>
            <span className="font-display text-2xl text-primary tabular-nums">{formatCurrency(deposit)}</span>
          </div>
        )}
      </ReservationTicket>

      <div className="flex flex-col sm:flex-row gap-3 mt-8 justify-center">
        <Link to="/" className="btn btn-primary">Về trang chủ</Link>
        <button type="button" onClick={onReset} className="btn btn-outline">Đặt thêm bàn khác</button>
      </div>
    </div>
  );
}
