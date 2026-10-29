import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { layDatBanTheoId } from "@/api/reservations.api";
import type { Reservation } from "@/types";
import ReservationSuccess from "./ReservationSuccess";

export default function ReservationPaymentResultPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const status = params.get("status");
  const reservationId = params.get("reservation_id");
  const [reservation, setReservation] = useState<Reservation | null>(null);
  const [loading, setLoading] = useState(status === "success" && Boolean(reservationId));

  useEffect(() => {
    if (status !== "success" || !reservationId) return;
    layDatBanTheoId(reservationId)
      .then(setReservation)
      .catch(() => setReservation(null))
      .finally(() => setLoading(false));
  }, [status, reservationId]);

  if (loading) {
    return <div className="max-w-lg mx-auto px-5 py-24 text-center text-muted">Đang xác nhận giao dịch với nhà hàng…</div>;
  }

  if (status === "success" && reservation?.depositStatus === "thanh_cong" && reservation.status === "cho_xac_nhan") {
    return <ReservationSuccess reservation={reservation} onReset={() => navigate("/dat-ban")} />;
  }

  const heading = status === "failed" ? "Thanh toán chưa thành công" : "Chưa xác nhận được thanh toán";
  return (
    <div className="max-w-lg mx-auto px-5 py-24 text-center">
      <h1 className="font-display text-3xl mb-3">{heading}</h1>
      <p className="text-muted mb-7">
        {status === "failed"
          ? "Giao dịch bị từ chối hoặc đã hết hạn. Đặt bàn chưa được xác nhận."
          : "Vui lòng đăng nhập đúng tài khoản đặt bàn rồi tải lại trang để kiểm tra trạng thái."}
      </p>
      <Link to="/tai-khoan" className="btn btn-primary">Vào tài khoản</Link>
      <Link to="/dat-ban" className="btn btn-outline ml-3">Quay lại đặt bàn</Link>
    </div>
  );
}
