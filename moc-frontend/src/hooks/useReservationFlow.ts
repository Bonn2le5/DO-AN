import { useCallback, useEffect, useState } from "react";
import {
  layDanhSachBan,
  layChinhSachDatCoc,
  giuBan,
  taoDatBan,
  taoPhienThanhToanVNPay,
} from "@/api/reservations.api";
import type {
  RestaurantTable,
  ReservationFoodItem,
  DepositPolicy,
  Reservation,
  VNPayPaymentSession,
  Food,
} from "@/types";
import { localDateInputValue } from "@/lib/utils";

export type ReservationStep = "branch_time" | "food" | "contact" | "success";

export interface ContactInfo {
  name: string;
  phone: string;
  note?: string;
}

export function useReservationFlow() {
  const [step, setStep] = useState<ReservationStep>("branch_time");

  // Branch + time selection state (new)
  const [selectedBranchId, setSelectedBranchIdState] = useState("");
  const [selectedBranchName, setSelectedBranchName] = useState("");

  const [date, setDateState] = useState(localDateInputValue);
  const [time, setTimeState] = useState("");
  const [partySize, setPartySizeState] = useState(2);

  const [tables, setTables] = useState<RestaurantTable[]>([]);
  const [tablesLoading, setTablesLoading] = useState(true);
  const [selectedTableId, setSelectedTableId] = useState<string | null>(null);
  const [holdInfo, setHoldInfo] = useState<{ holdId: string; heldUntil: string } | null>(null);
  const [holdLoading, setHoldLoading] = useState(false);
  const [holdError, setHoldError] = useState("");

  const [policy, setPolicy] = useState<DepositPolicy | null>(null);
  const [foodItems, setFoodItems] = useState<ReservationFoodItem[]>([]);
  const [foodCategory, setFoodCategory] = useState("all");
  const [contact, setContact] = useState<ContactInfo>({ name: "", phone: "", note: "" });
  const [paymentMethod, setPaymentMethod] = useState<"vnpay">("vnpay");

  const [reservation, setReservation] = useState<Reservation | null>(null);
  const [paymentSession, setPaymentSession] = useState<VNPayPaymentSession | null>(null);
  const [paymentError, setPaymentError] = useState("");
  const [retryingPayment, setRetryingPayment] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let active = true;
    layDanhSachBan(selectedBranchId || undefined)
      .then((result) => { if (active) setTables(result); })
      .finally(() => { if (active) setTablesLoading(false); });
    return () => { active = false; };
  }, [selectedBranchId]);

  useEffect(() => {
    layChinhSachDatCoc(selectedBranchId || undefined).then(setPolicy);
  }, [selectedBranchId]);

  const setDate = (value: string) => {
    setDateState(value);
    setSelectedTableId(null);
    setHoldInfo(null);
  };

  const setSelectedBranchId = (value: string) => {
    setTablesLoading(true);
    setSelectedBranchIdState(value);
    setSelectedTableId(null);
    setHoldInfo(null);
  };

  const setTime = (value: string) => {
    setTimeState(value);
    setSelectedTableId(null);
    setHoldInfo(null);
  };

  const setPartySize = (value: number) => {
    setPartySizeState(value);
    setSelectedTableId(null);
    setHoldInfo(null);
  };

  const selectedTable = tables.find((b) => b.id === selectedTableId) ?? null;

  const foodSubtotal = foodItems.reduce(
    (total, i) => total + (i.food.price ?? i.food.donGia ?? 0) * (i.quantity ?? 1),
    0
  );

  const depositPercent = policy?.depositPercentage ?? 20;
  const depositAmount = foodItems.length > 0
    ? Math.round((foodSubtotal * depositPercent) / 100)
    : 0;

  // Proceed from branch_time step
  const proceedFromBranchTime = (branchId: string, branchName: string, selectedTime: string) => {
    // The selected table hold belongs to this branch/time. Do not call the
    // branch/time setters here: they intentionally clear the hold token.
    setSelectedBranchIdState(branchId);
    setSelectedBranchName(branchName);
    setTimeState(selectedTime);
    setStep("food");
  };

  const selectTable = async (tableId: string) => {
    setSelectedTableId(tableId);
    setHoldInfo(null);
    setHoldError("");
    setHoldLoading(true);
    try {
      const res = await giuBan({
        idBan: tableId,
        ngayDat: date,
        gioDat: time,
        soLuongKhach: partySize,
      });
      setHoldInfo({ holdId: res.idGiuBan, heldUntil: res.thoiHanGiuCho });
    } catch (e: any) {
      setHoldError(e.response?.data?.chi_tiet ?? "Bàn đang có người giữ hoặc đặt.");
      setSelectedTableId(null);
    } finally {
      setHoldLoading(false);
    }
  };

  const proceedToContact = () => setStep("contact");

  const updateContact = useCallback((values: Partial<ContactInfo>) => {
    setContact((current) => ({ ...current, ...values }));
  }, []);

  const addFood = (food: Food) => {
    setFoodItems((cur) => {
      const existing = cur.find((i) => i.food.id === food.id);
      if (existing) {
        return cur.map((i) =>
          i.food.id === food.id ? { ...i, quantity: i.quantity + 1 } : i
        );
      }
      return [...cur, { food, quantity: 1 }];
    });
  };

  const updateFoodQty = (foodId: string, quantity: number) => {
    if (quantity <= 0) {
      setFoodItems((cur) => cur.filter((i) => i.food.id !== foodId));
      return;
    }
    setFoodItems((cur) =>
      cur.map((i) => (i.food.id === foodId ? { ...i, quantity } : i))
    );
  };

  const submitContact = async (contact: ContactInfo) => {
    setSubmitting(true);
    try {
      const res = await taoDatBan({
        idGiuBan: holdInfo?.holdId,
        idBan: selectedTableId ?? undefined,
        chiNhanhId: selectedBranchId || undefined,
        ngayDat: date,
        gioDat: time,
        soLuongKhach: partySize,
        hinhThuc: foodItems.length ? "table_and_food" : "table_only",
        danhSachMon: foodItems,
        tenKhachHang: contact.name,
        soDienThoai: contact.phone,
        ghiChu: contact.note,
      });
      setReservation(res);

      if (res.depositAmount > 0) {
        try {
          const session = await taoPhienThanhToanVNPay(res.id);
          setPaymentSession(session);
        } catch (err: any) {
          setPaymentError(err.response?.data?.detail ?? "Đặt bàn đã được ghi nhận nhưng chưa tạo được phiên thanh toán.");
        }
      } else {
        setStep("success");
      }
    } catch (err: any) {
      alert(err.response?.data?.chi_tiet ?? err.response?.data?.detail ?? "Không thể tạo đơn đặt bàn. Vui lòng thử lại.");
    } finally {
      setSubmitting(false);
    }
  };

  const retryPayment = async () => {
    if (!reservation) return;
    setRetryingPayment(true);
    setPaymentError("");
    try {
      const session = await taoPhienThanhToanVNPay(reservation.id);
      setPaymentSession(session);
    } catch (err: any) {
      setPaymentError(err.response?.data?.detail ?? "Chưa tạo được phiên thanh toán. Vui lòng thử lại.");
    } finally {
      setRetryingPayment(false);
    }
  };

  const reset = () => {
    setStep("branch_time");
    setSelectedBranchId("");
    setSelectedBranchName("");
    setSelectedTableId(null);
    setHoldInfo(null);
    setFoodItems([]);
    setFoodCategory("all");
    setContact({ name: "", phone: "", note: "" });
    setPaymentMethod("vnpay");
    setReservation(null);
    setPaymentSession(null);
    setPaymentError("");
  };

  return {
    // English properties
    step,
    setStep,
    // Branch state
    selectedBranchId,
    setSelectedBranchId,
    selectedBranchName,
    setSelectedBranchName,
    proceedFromBranchTime,
    // Date/time/party
    date,
    setDate,
    time,
    setTime,
    partySize,
    setPartySize,
    tables,
    tablesLoading,
    selectedTableId,
    selectedTable,
    holdInfo,
    holdLoading,
    holdError,
    selectTable,
    proceedToContact,
    policy,
    foodItems,
    foodCategory,
    setFoodCategory,
    addFood,
    updateFoodQty,
    foodSubtotal,
    depositAmount,
    submitContact,
    contact,
    updateContact,
    paymentMethod,
    setPaymentMethod,
    submitting,
    reservation,
    paymentSession,
    paymentError,
    retryingPayment,
    retryPayment,
    reset,

    // Vietnamese aliases
    buocHienTai: step,
    setBuocHienTai: setStep,
    ngayDat: date,
    setNgayDat: setDate,
    gioDat: time,
    setGioDat: setTime,
    soLuongKhach: partySize,
    setSoLuongKhach: setPartySize,
    danhSachBan: tables,
    dangTaiBan: tablesLoading,
    idBanDaChon: selectedTableId,
    banDaChon: selectedTable,
    thongTinGiuBan: holdInfo,
    dangGiuBan: holdLoading,
    loiGiuBan: holdError,
    chonBan: selectTable,
    tiepTucSauChonBan: proceedToContact,
    chinhSachCoc: policy,
    danhSachMonDat: foodItems,
    themMonVaoDatBan: addFood,
    capNhatSoLuongMon: updateFoodQty,
    tienMonAn: foodSubtotal,
    soTienCoc: depositAmount,
    guiThongTinLienHe: (info: any) => submitContact({ name: info.tenKhachHang ?? info.name, phone: info.soDienThoai ?? info.phone, note: info.ghiChu ?? info.note }),
    dangGuiDon: submitting,
    thongTinDatBan: reservation,
    phienThanhToan: paymentSession,
    loiThanhToan: paymentError,
    dangThuLaiThanhToan: retryingPayment,
    thuLaiThanhToan: retryPayment,
    datLai: reset,
  };
}
