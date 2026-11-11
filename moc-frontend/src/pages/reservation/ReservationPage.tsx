import { useEffect } from "react";
import { ChevronLeft } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { useReservationFlow } from "@/hooks/useReservationFlow";
import ReservationStepper from "./ReservationStepper";
import BranchTimeStep from "./BranchTimeStep";
import FoodStep from "./FoodStep";
import ContactStep from "./ContactStep";
import PaymentStep from "./PaymentStep";
import ReservationSuccess from "./ReservationSuccess";

const HEADINGS = {
  branch_time: "Chọn chi nhánh, ngày và giờ",
  food: "Gọi món trước, hoặc bỏ qua",
  contact: "Xác nhận đặt chỗ",
} as const;

export default function ReservationPage() {
  const flow = useReservationFlow();
  const isAuthenticated = useAuthStore((state) => state.daDangNhap);

  // Mỗi lần đổi bước, đưa người dùng về đầu trang.
  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [flow.buocHienTai]);

  if (!isAuthenticated) {
    return (
      <div className="reservation-ui max-w-lg mx-auto px-5 py-24 text-center">
        <h1 className="font-display text-3xl mb-3">Đăng nhập để đặt bàn</h1>
        <p className="text-muted mb-7">Tài khoản giúp bạn theo dõi đặt chỗ và thanh toán cọc.</p>
        <Link to="/dang-nhap" state={{ from: "/dat-ban" }} className="btn btn-primary">Đăng nhập</Link>
      </div>
    );
  }

  if (flow.buocHienTai === "success" && flow.thongTinDatBan) {
    return <ReservationSuccess reservation={flow.thongTinDatBan} branchName={flow.tenChiNhanhDaChon} onReset={flow.datLai} />;
  }

  const date = new Date(`${flow.ngayDat}T12:00:00`);
  const isWeekend = date.getDay() === 5 || date.getDay() === 6;
  const highPeak = isWeekend && flow.gioDat >= "18:00" && flow.gioDat < "21:00";
  const canGoBack = (flow.buocHienTai === "food" || flow.buocHienTai === "contact") && !flow.thongTinDatBan;
  const step = flow.buocHienTai === "success" ? "contact" : flow.buocHienTai;
  // Bước xác nhận (form) phải vừa một màn hình nên thu gọn phần đầu trang.
  const compact = flow.buocHienTai === "contact" && !flow.thongTinDatBan;

  return (
    <div className={`reservation-ui max-w-275 mx-auto px-4 sm:px-5 md:px-8 ${compact ? "pt-4 lg:pt-6 pb-10" : "pt-8 sm:pt-12 pb-16"}`}>
      {canGoBack && (
        <button
          type="button"
          onClick={() => flow.setBuocHienTai(flow.buocHienTai === "food" ? "branch_time" : "food")}
          className={`items-center gap-1 text-sm font-semibold text-muted hover:text-primary ${compact ? "hidden lg:inline-flex mb-1" : "inline-flex mb-4"}`}
        >
          <ChevronLeft size={18} /> {flow.buocHienTai === "food" ? "Đổi giờ hẹn" : "Sửa món"}
        </button>
      )}

      <h1 className={`font-display leading-tight ${compact ? "max-lg:sr-only text-[28px] mb-3" : "text-[30px] sm:text-[40px] mb-6"}`}>{HEADINGS[step]}</h1>
      <ReservationStepper current={flow.buocHienTai} compact={compact} />

      {flow.buocHienTai === "branch_time" && (
        <BranchTimeStep
          selectedBranchId={flow.idChiNhanhDaChon}
          onBranchChange={flow.setIdChiNhanhDaChon}
          date={flow.ngayDat}
          onDateChange={flow.setNgayDat}
          partySize={flow.soLuongKhach}
          onPartySizeChange={flow.setSoLuongKhach}
          selectedTime={flow.gioDat}
          onTimeSelect={flow.setGioDat}
          onContinue={flow.tiepTucSauChonGio}
        />
      )}

      {flow.buocHienTai === "food" && (
        <FoodStep
          foodItems={flow.danhSachMonDat}
          onAdd={flow.themMonVaoDatBan}
          onAddMany={flow.themNhieuMonVaoDatBan}
          onUpdateQty={flow.capNhatSoLuongMon}
          subtotal={flow.tienMonAn}
          depositAmount={flow.soTienCoc}
          depositPercentage={flow.chinhSachCoc?.phanTramCoc ?? 20}
          activeCategory={flow.danhMucDangLoc}
          onCategoryChange={flow.setDanhMucDangLoc}
          highPeak={highPeak}
          time={flow.gioDat}
          date={flow.ngayDat}
          partySize={flow.soLuongKhach}
          branchName={flow.tenChiNhanhDaChon}
          onContinue={flow.tiepTucSauChonBan}
        />
      )}

      {flow.buocHienTai === "contact" && flow.thongTinDatBan && flow.thongTinDatBan.soTienCoc > 0 && (
        <PaymentStep
          reservation={flow.thongTinDatBan}
          branchName={flow.tenChiNhanhDaChon}
          paymentSession={flow.phienThanhToan}
          error={flow.loiThanhToan}
          retrying={flow.dangThuLaiThanhToan}
          onRetry={flow.thuLaiThanhToan}
        />
      )}

      {flow.buocHienTai === "contact" && !flow.thongTinDatBan && (
        <ContactStep
          branchName={flow.tenChiNhanhDaChon}
          date={flow.ngayDat}
          time={flow.gioDat}
          partySize={flow.soLuongKhach}
          foodItems={flow.danhSachMonDat}
          foodSubtotal={flow.tienMonAn}
          depositAmount={flow.soTienCoc}
          depositPercentage={flow.chinhSachCoc?.phanTramCoc ?? 20}
          policy={flow.chinhSachCoc}
          initialValues={flow.thongTinLienHe}
          paymentMethod={flow.phuongThucThanhToan}
          onPaymentMethodChange={flow.setPhuongThucThanhToan}
          onValuesChange={flow.capNhatThongTinLienHe}
          submitting={flow.dangGuiDon}
          onSubmit={flow.guiThongTinLienHe}
          onEditTime={() => flow.setBuocHienTai("branch_time")}
          onEditFood={() => flow.setBuocHienTai("food")}
        />
      )}
    </div>
  );
}
