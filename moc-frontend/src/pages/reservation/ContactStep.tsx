import { useEffect, useState, type ReactNode } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { MapPin, ShieldCheck, Users } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import type { MonAnDatBan, ChinhSachDatCoc } from "@/types";
import type { ThongTinLienHe } from "@/hooks/useReservationFlow";
import { formatLongDate, refundLabel } from "./ReservationTicket";

const schema = z.object({
  tenKhachHang: z.string().trim().min(2, "Nhập họ và tên để nhà hàng liên hệ."),
  soDienThoai: z.string().regex(/^0\d{9}$/, "Nhập số điện thoại gồm 10 số, bắt đầu bằng 0."),
  ghiChu: z.string().optional(),
});
type FormData = z.infer<typeof schema>;

interface ContactStepProps {
  branchName: string;
  date: string;
  time: string;
  partySize: number;
  foodItems: MonAnDatBan[];
  foodSubtotal: number;
  depositAmount: number;
  depositPercentage: number;
  policy: ChinhSachDatCoc | null;
  initialValues: ThongTinLienHe;
  paymentMethod: "vnpay";
  onPaymentMethodChange: (method: "vnpay") => void;
  onValuesChange: (values: Partial<ThongTinLienHe>) => void;
  submitting: boolean;
  onSubmit: (data: FormData) => Promise<void>;
  onEditTime: () => void;
  onEditFood: () => void;
}

export default function ContactStep({
  branchName, date, time, partySize, foodItems, foodSubtotal, depositAmount,
  depositPercentage, policy, initialValues, paymentMethod, onPaymentMethodChange,
  onValuesChange, submitting, onSubmit, onEditTime, onEditFood,
}: ContactStepProps) {
  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: initialValues,
  });

  useEffect(() => {
    const subscription = watch((values) => onValuesChange(values));
    return () => subscription.unsubscribe();
  }, [watch, onValuesChange]);

  const [showNote, setShowNote] = useState(Boolean(initialValues.ghiChu));
  const needsDeposit = foodItems.length > 0 && depositAmount > 0;
  const expiryMinutes = policy?.hanThanhToanPhut ?? 15;
  const dishCount = foodItems.reduce((total, item) => total + item.soLuong, 0);
  const submitLabel = submitting ? "Đang gửi đặt chỗ…" : needsDeposit ? `Đặt chỗ và cọc ${formatCurrency(depositAmount)}` : "Xác nhận đặt chỗ";
  const afterSubmit = needsDeposit
    ? `Bạn có ${expiryMinutes} phút để thanh toán cọc qua VNPay. Nhà hàng sẽ gọi điện xác nhận.`
    : "Nhà hàng sẽ gọi điện xác nhận. Bạn gọi món tại bàn khi đến.";

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="reservation-confirm pb-24 lg:pb-0">
      <div className="bg-white rounded-[20px] border border-black/[0.07] shadow-soft grid grid-cols-[minmax(0,1fr)] lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)_minmax(0,1fr)] lg:h-[clamp(470px,calc(100dvh-240px),620px)] divide-y lg:divide-y-0 lg:divide-x divide-black/[0.08]">

        {/* Cột 1: liên hệ + thông tin đặt bàn */}
        <div className="flex flex-col divide-y divide-black/[0.08] min-h-0">
          <section className="p-4 lg:p-5 space-y-3" aria-labelledby="sec-contact">
            <div className="flex items-center justify-between gap-3">
              <SectionTitle id="sec-contact">Thông tin liên hệ</SectionTitle>
              {!showNote && (
                <button type="button" onClick={() => setShowNote(true)} className="text-sm font-semibold text-primary">+ Ghi chú</button>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Field id="reservation-name" label="Họ và tên" compactLabel error={errors.tenKhachHang?.message}>
                <input id="reservation-name" autoComplete="name" placeholder="Họ và tên" {...register("tenKhachHang")} aria-invalid={!!errors.tenKhachHang} className={cn("reservation-field py-2.5!", errors.tenKhachHang && "border-primary")} />
              </Field>
              <Field id="reservation-phone" label="Số điện thoại" compactLabel error={errors.soDienThoai?.message}>
                <input id="reservation-phone" type="tel" inputMode="numeric" autoComplete="tel" placeholder="Số điện thoại" {...register("soDienThoai")} aria-invalid={!!errors.soDienThoai} className={cn("reservation-field py-2.5!", errors.soDienThoai && "border-primary")} />
              </Field>
            </div>
            {showNote && (
              <Field id="reservation-note" label="Ghi chú" optional compactLabel>
                <input id="reservation-note" autoFocus={!initialValues.ghiChu} {...register("ghiChu")} placeholder="Ghi chú, ví dụ: có trẻ em, cần ghế em bé" className="reservation-field py-2.5!" />
              </Field>
            )}
          </section>

          <section className="p-4 lg:p-5 flex-1" aria-labelledby="sec-booking">
            <div className="flex items-center justify-between gap-3">
              <SectionTitle id="sec-booking">Thông tin đặt bàn</SectionTitle>
              <EditLink onClick={onEditTime} label="Sửa giờ hẹn" />
            </div>
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 mt-1.5 lg:mt-2">
              <span className="text-[26px] lg:text-[40px] font-bold leading-none tracking-[-0.03em] text-primary tabular-nums">{time.slice(0, 5)}</span>
              <span className="font-semibold">{formatLongDate(date)}</span>
            </div>
            <div className="mt-2 lg:mt-3 text-sm max-lg:flex max-lg:items-center max-lg:gap-3 max-lg:min-w-0 lg:space-y-1.5">
              <div className="flex gap-2 shrink-0"><Users size={16} className="text-muted shrink-0 mt-0.5" /><span>{partySize} khách<span className="text-muted hidden lg:inline">, nhân viên xếp bàn khi bạn đến</span></span></div>
              {branchName && <div className="flex gap-2 min-w-0"><MapPin size={16} className="text-muted shrink-0 mt-0.5" /><span className="max-lg:truncate">{branchName}</span></div>}
            </div>
          </section>
        </div>

        {/* Cột 2: món đặt trước, tự cuộn khi nhiều món */}
        <section className="p-4 lg:p-5 flex flex-col min-h-0" aria-labelledby="sec-food">
          <div className="flex items-center justify-between gap-3 mb-3">
            <SectionTitle id="sec-food">Món đặt trước{dishCount > 0 && <span className="text-muted font-normal"> ({dishCount} món)</span>}</SectionTitle>
            <EditLink onClick={onEditFood} label="Sửa món đã chọn" text={dishCount > 0 ? "Sửa" : "Thêm món"} />
          </div>
          {foodItems.length === 0 ? (
            <p className="text-sm text-muted">Bạn chỉ giữ chỗ và gọi món tại nhà hàng.</p>
          ) : (
            <>
              <ul className="flex-1 min-h-0 max-h-[92px] lg:max-h-none overflow-y-auto -mr-3 pr-3 divide-y divide-black/[0.06] overscroll-contain" tabIndex={0} aria-label="Danh sách món">
                {foodItems.map(({ monAn: food, soLuong: quantity }) => (
                  <li key={food.id} className="flex items-baseline gap-3 py-1.5 lg:py-2 text-sm">
                    <span className="w-6 shrink-0 text-muted tabular-nums">{quantity}×</span>
                    <span className="flex-1 min-w-0">{food.tenMon}</span>
                    <span className="tabular-nums">{formatCurrency((food.donGia ?? 0) * quantity)}</span>
                  </li>
                ))}
              </ul>
              <div className="flex justify-between gap-3 pt-3 mt-1 border-t border-black/[0.12] text-sm">
                <span className="text-muted">Tổng tiền món</span>
                <span className="font-semibold tabular-nums">{formatCurrency(foodSubtotal)}</span>
              </div>
            </>
          )}
        </section>

        {/* Cột 3: thanh toán + nút xác nhận */}
        <section className="p-4 lg:p-5 flex flex-col min-h-0" aria-labelledby="sec-payment">
          <SectionTitle id="sec-payment">Thông tin thanh toán</SectionTitle>
          <div className="flex-1 min-h-0 overflow-y-auto mt-2 lg:mt-3 space-y-2 lg:space-y-3">
            {needsDeposit ? (
              <>
                <div className="lg:rounded-xl lg:bg-primary/[0.06] lg:p-4">
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="font-semibold">Tiền cọc <span className="text-muted font-normal lg:hidden">({depositPercentage}% tiền món)</span></span>
                    <span className="text-xl lg:text-2xl font-bold tracking-[-0.02em] text-primary tabular-nums">{formatCurrency(depositAmount)}</span>
                  </div>
                  <p className="hidden lg:block text-xs text-muted mt-1">{depositPercentage}% tiền món, trừ vào hoá đơn khi bạn dùng bữa.</p>
                  <p className="lg:hidden text-xs text-muted mt-0.5">Trả qua VNPay trong {expiryMinutes} phút, trừ vào hoá đơn.</p>
                </div>
                <label className="hidden lg:flex gap-3 items-start rounded-xl border border-primary/40 bg-primary/[0.03] p-3 cursor-pointer">
                  <input type="radio" name="reservation-payment" checked={paymentMethod === "vnpay"} onChange={() => onPaymentMethodChange("vnpay")} className="mt-1 accent-primary" />
                  <span className="flex-1 text-sm">
                    <strong className="block">VNPay</strong>
                    <span className="text-muted">Thẻ ngân hàng hoặc quét QR</span>
                  </span>
                  <ShieldCheck size={18} className="text-muted shrink-0 mt-0.5" />
                </label>
                {policy && policy.quyTacHuyBan.length > 0 && (
                  <details className="group text-sm">
                    <summary className="cursor-pointer font-semibold text-primary list-none">
                      <span className="group-open:hidden">Xem điều kiện hoàn cọc</span>
                      <span className="hidden group-open:inline">Ẩn điều kiện hoàn cọc</span>
                    </summary>
                    <ul className="mt-2 space-y-1">
                      {policy.quyTacHuyBan.map((rule) => (
                        <li key={rule.mocThoiGian} className="flex justify-between gap-3 text-xs">
                          <span className="text-muted">{refundLabel(rule.mocThoiGian ?? "")}</span>
                          <span className="font-semibold shrink-0">{rule.phanTramHoanTien > 0 ? `Hoàn ${rule.phanTramHoanTien}%` : "Không hoàn"}</span>
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
              </>
            ) : (
              <div className="rounded-xl bg-black/[0.03] p-4">
                <div className="font-semibold">Không cần đặt cọc</div>
                <p className="text-sm text-muted mt-1">Bạn thanh toán tại nhà hàng sau bữa ăn.</p>
              </div>
            )}
          </div>

          <div className="hidden lg:block pt-4">
            <button type="submit" disabled={submitting} className="btn btn-primary w-full disabled:opacity-60">{submitLabel}</button>
            <p className="text-xs text-muted mt-2.5 text-center">{afterSubmit}</p>
          </div>
          
        </section>
      </div>

      {/* Nút xác nhận cố định ở đáy màn hình trên mobile/tablet */}
      <div className="reservation-sticky-bar lg:hidden fixed inset-x-0 bottom-0 z-30 border-t border-black/10 bg-bg/95 backdrop-blur px-4 py-3">
        <div className="max-w-xl mx-auto">
          <button type="submit" disabled={submitting} className="btn btn-primary w-full py-3! disabled:opacity-60">{submitLabel}</button>
        </div>
      </div>
    </form>
  );
}

function SectionTitle({ id, children }: { id: string; children: ReactNode }) {
  return <h3 id={id} className="text-[15px] font-semibold">{children}</h3>;
}

function EditLink({ onClick, label, text = "Sửa" }: { onClick: () => void; label: string; text?: string }) {
  return (
    <button type="button" onClick={onClick} aria-label={label} className="text-sm font-semibold text-primary underline underline-offset-4 decoration-primary/30 hover:decoration-primary shrink-0">
      {text}
    </button>
  );
}

function Field({ id, label, hint, optional, compactLabel, error, children }: {
  id: string; label: string; hint?: string; optional?: boolean; compactLabel?: boolean; error?: string; children: ReactNode;
}) {
  return (
    <div>
      <label htmlFor={id} className={cn("text-[13px] font-medium text-muted block mb-1", compactLabel && "max-lg:sr-only")}>
        {label}{optional && <span className="text-muted font-normal"> (không bắt buộc)</span>}
      </label>
      {children}
      {error ? <p className="text-xs text-primary mt-1" role="alert">{error}</p> : hint && <p className="text-xs text-muted mt-1.5">{hint}</p>}
    </div>
  );
}
