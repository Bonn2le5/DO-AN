import { useCallback, useEffect, useState } from "react";
import {
  layChinhSachDatCoc,
  taoDatBan,
  taoPhienThanhToanVNPay,
} from "@/api/reservations.api";
import type {
  MonAnDatBan,
  ChinhSachDatCoc,
  ThongTinDatBan,
  PhienThanhToanVNPay,
  MonAn,
} from "@/types";
import { localDateInputValue } from "@/lib/utils";

export type BuocDatBan = "branch_time" | "food" | "contact" | "success";

export interface ThongTinLienHe {
  tenKhachHang: string;
  soDienThoai: string;
  ghiChu?: string;
}

export function useReservationFlow() {
  const [buocHienTai, setBuocHienTai] = useState<BuocDatBan>("branch_time");

  // Branch + time selection state (new)
  const [idChiNhanhDaChon, setSelectedBranchIdState] = useState("");
  const [tenChiNhanhDaChon, setTenChiNhanhDaChon] = useState("");

  const [ngayDat, setDateState] = useState(localDateInputValue);
  const [gioDat, setTimeState] = useState("");
  const [soLuongKhach, setPartySizeState] = useState(2);

  const [chinhSachCoc, setPolicy] = useState<ChinhSachDatCoc | null>(null);
  const [danhSachMonDat, setFoodItems] = useState<MonAnDatBan[]>([]);
  const [danhMucDangLoc, setDanhMucDangLoc] = useState("all");
  const [thongTinLienHe, setContact] = useState<ThongTinLienHe>({ tenKhachHang: "", soDienThoai: "", ghiChu: "" });
  const [phuongThucThanhToan, setPhuongThucThanhToan] = useState<"vnpay">("vnpay");

  const [thongTinDatBan, setReservation] = useState<ThongTinDatBan | null>(null);
  const [phienThanhToan, setPaymentSession] = useState<PhienThanhToanVNPay | null>(null);
  const [loiThanhToan, setPaymentError] = useState("");
  const [dangThuLaiThanhToan, setRetryingPayment] = useState(false);
  const [dangGuiDon, setSubmitting] = useState(false);

  useEffect(() => {
    layChinhSachDatCoc(idChiNhanhDaChon || undefined).then(setPolicy);
  }, [idChiNhanhDaChon]);

  const setNgayDat = (value: string) => {
    setDateState(value);
  };

  const setIdChiNhanhDaChon = (value: string) => {
    setSelectedBranchIdState(value);
  };

  const setGioDat = (value: string) => {
    setTimeState(value);
  };

  const setSoLuongKhach = (value: number) => {
    setPartySizeState(value);
  };

  const tienMonAn = danhSachMonDat.reduce(
    (total, i) => total + (i.monAn.donGia ?? 0) * (i.soLuong ?? 1),
    0
  );

  const depositPercent = chinhSachCoc?.phanTramCoc ?? 20;
  const soTienCoc = danhSachMonDat.length > 0
    ? Math.round((tienMonAn * depositPercent) / 100)
    : 0;

  // Proceed from branch_time step
  const tiepTucSauChonGio = (branchId: string, branchName: string, selectedTime: string) => {
    setSelectedBranchIdState(branchId);
    setTenChiNhanhDaChon(branchName);
    setTimeState(selectedTime);
    setBuocHienTai("food");
  };

  const tiepTucSauChonBan = () => setBuocHienTai("contact");

  const capNhatThongTinLienHe = useCallback((values: Partial<ThongTinLienHe>) => {
    setContact((current) => ({ ...current, ...values }));
  }, []);

  const themMonVaoDatBan = (food: MonAn) => {
    setFoodItems((cur) => {
      const existing = cur.find((i) => i.monAn.id === food.id);
      if (existing) {
        return cur.map((i) =>
          i.monAn.id === food.id ? { ...i, soLuong: i.soLuong + 1 } : i
        );
      }
      return [...cur, { monAn: food, soLuong: 1 }];
    });
  };

  const capNhatSoLuongMon = (foodId: string, quantity: number) => {
    if (quantity <= 0) {
      setFoodItems((cur) => cur.filter((i) => i.monAn.id !== foodId));
      return;
    }
    setFoodItems((cur) =>
      cur.map((i) => (i.monAn.id === foodId ? { ...i, soLuong: quantity } : i))
    );
  };

  const guiThongTinLienHe = async (contact: ThongTinLienHe) => {
    setSubmitting(true);
    try {
      const res = await taoDatBan({
        chiNhanhId: idChiNhanhDaChon || undefined,
        ngayDat: ngayDat,
        gioDat: gioDat,
        soLuongKhach: soLuongKhach,
        hinhThuc: danhSachMonDat.length ? "table_and_food" : "table_only",
        danhSachMon: danhSachMonDat,
        tenKhachHang: contact.tenKhachHang,
        soDienThoai: contact.soDienThoai,
        ghiChu: contact.ghiChu,
      });
      setReservation(res);

      if (res.soTienCoc > 0) {
        try {
          const session = await taoPhienThanhToanVNPay(res.id);
          setPaymentSession(session);
        } catch (err: any) {
          setPaymentError(err.response?.data?.detail ?? "Đặt bàn đã được ghi nhận nhưng chưa tạo được phiên thanh toán.");
        }
      } else {
        setBuocHienTai("success");
      }
    } catch (err: any) {
      alert(err.response?.data?.chi_tiet ?? err.response?.data?.detail ?? "Không thể tạo đơn đặt bàn. Vui lòng thử lại.");
    } finally {
      setSubmitting(false);
    }
  };

  const thuLaiThanhToan = async () => {
    if (!thongTinDatBan) return;
    setRetryingPayment(true);
    setPaymentError("");
    try {
      const session = await taoPhienThanhToanVNPay(thongTinDatBan.id);
      setPaymentSession(session);
    } catch (err: any) {
      setPaymentError(err.response?.data?.detail ?? "Chưa tạo được phiên thanh toán. Vui lòng thử lại.");
    } finally {
      setRetryingPayment(false);
    }
  };

  const datLai = () => {
    setBuocHienTai("branch_time");
    setIdChiNhanhDaChon("");
    setTenChiNhanhDaChon("");
    setFoodItems([]);
    setDanhMucDangLoc("all");
    setContact({ tenKhachHang: "", soDienThoai: "", ghiChu: "" });
    setPhuongThucThanhToan("vnpay");
    setReservation(null);
    setPaymentSession(null);
    setPaymentError("");
  };

  return {
    buocHienTai,
    setBuocHienTai,
    idChiNhanhDaChon,
    setIdChiNhanhDaChon,
    tenChiNhanhDaChon,
    setTenChiNhanhDaChon,
    tiepTucSauChonGio,
    ngayDat,
    setNgayDat,
    gioDat,
    setGioDat,
    soLuongKhach,
    setSoLuongKhach,
    tiepTucSauChonBan,
    chinhSachCoc,
    danhSachMonDat,
    danhMucDangLoc,
    setDanhMucDangLoc,
    themMonVaoDatBan,
    capNhatSoLuongMon,
    tienMonAn,
    soTienCoc,
    guiThongTinLienHe,
    thongTinLienHe,
    capNhatThongTinLienHe,
    phuongThucThanhToan,
    setPhuongThucThanhToan,
    dangGuiDon,
    thongTinDatBan,
    phienThanhToan,
    loiThanhToan,
    dangThuLaiThanhToan,
    thuLaiThanhToan,
    datLai,
  };
}
