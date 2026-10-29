import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { formatCurrency } from "@/lib/utils";
import type { RestaurantTable, ReservationFoodItem, DepositPolicy } from "@/types";
import type { ContactInfo } from "@/hooks/useReservationFlow";

const schema = z.object({
  name: z.string().trim().min(2, "Nhập họ và tên để nhà hàng liên hệ."),
  phone: z.string().regex(/^0\d{9}$/, "Nhập số điện thoại gồm 10 số, bắt đầu bằng 0."),
  note: z.string().optional(),
});
type FormData = z.infer<typeof schema>;

interface ContactStepProps {
  table: RestaurantTable | null;
  date: string;
  time: string;
  partySize: number;
  foodItems: ReservationFoodItem[];
  foodSubtotal: number;
  depositAmount: number;
  depositPercentage: number;
  policy: DepositPolicy | null;
  initialValues: ContactInfo;
  paymentMethod: "vnpay";
  onPaymentMethodChange: (method: "vnpay") => void;
  onValuesChange: (values: Partial<ContactInfo>) => void;
  submitting: boolean;
  onSubmit: (data: FormData) => Promise<void>;
}

export default function ContactStep({
  table, date, time, partySize, foodItems, foodSubtotal, depositAmount,
  depositPercentage, policy, initialValues, paymentMethod, onPaymentMethodChange,
  onValuesChange, submitting, onSubmit,
}: ContactStepProps) {
  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: initialValues,
  });

  useEffect(() => {
    const subscription = watch((values) => onValuesChange(values));
    return () => subscription.unsubscribe();
  }, [watch, onValuesChange]);

  return (
    <div>
      <h2 className="font-display text-3xl mb-2">Xác nhận đặt chỗ</h2>
      <p className="text-muted mb-7">Nhập thông tin liên hệ. Nhà hàng sẽ gọi điện xác nhận với bạn.</p>

      <form onSubmit={handleSubmit(onSubmit)} className="grid lg:grid-cols-[1fr_400px] gap-8">
        <div className="space-y-5">
          <section className="card p-5 md:p-6 space-y-4">
            <div>
              <label htmlFor="reservation-name" className="text-sm font-semibold block mb-2">Họ và tên</label>
              <input id="reservation-name" {...register("name")} className="w-full px-4 py-3 rounded-xl border border-black/15 bg-white outline-none focus:border-primary" />
              {errors.name && <p className="text-sm text-primary mt-1.5">{errors.name.message}</p>}
            </div>
            <div>
              <label htmlFor="reservation-phone" className="text-sm font-semibold block mb-2">Số điện thoại</label>
              <input id="reservation-phone" type="tel" inputMode="numeric" placeholder="Chọn số có Zalo" {...register("phone")} className="w-full px-4 py-3 rounded-xl border border-black/15 bg-white outline-none focus:border-primary" />
              {errors.phone && <p className="text-sm text-primary mt-1.5">{errors.phone.message}</p>}
            </div>
            <div>
              <label htmlFor="reservation-note" className="text-sm font-semibold block mb-2">Ghi chú <span className="text-muted font-normal">(không bắt buộc)</span></label>
              <textarea id="reservation-note" {...register("note")} placeholder="Ví dụ: có trẻ em, cần ghế em bé" rows={3} className="w-full px-4 py-3 rounded-xl border border-black/15 bg-white outline-none focus:border-primary resize-y" />
            </div>
          </section>
        </div>

        <aside className="space-y-4">
          <section className="card p-5 space-y-3">
            <h3 className="font-display text-xl">Tóm tắt đặt chỗ</h3>
            <SummaryRow label="Bàn" value={table?.label ?? "—"} />
            <SummaryRow label="Ngày" value={date} />
            <SummaryRow label="Giờ" value={time} />
            <SummaryRow label="Số khách" value={String(partySize)} />

            {foodItems.length > 0 && (
              <div className="pt-3 border-t border-black/8">
                <h4 className="font-semibold mb-2">Món đã gọi trước</h4>
                <div className="space-y-2">
                  {foodItems.map(({ food, quantity }) => (
                    <div key={food.id} className="flex justify-between gap-3 text-sm">
                      <span>{quantity} × {food.name}</span>
                      <span className="text-muted">{formatCurrency(food.price * quantity)}</span>
                    </div>
                  ))}
                </div>
                <div className="flex justify-between font-semibold mt-3 pt-3 border-t border-black/6">
                  <span>Tổng tiền món</span><span>{formatCurrency(foodSubtotal)}</span>
                </div>
              </div>
            )}
          </section>

          {foodItems.length > 0 && (
            <section className="card p-5 space-y-4">
              <h3 className="font-display text-xl">Thanh toán cọc</h3>
              <div className="flex justify-between gap-4 text-sm">
                <span className="text-muted">Cọc {depositPercentage}% tổng tiền món</span>
                <strong className="text-primary">{formatCurrency(depositAmount)}</strong>
              </div>
              <label className="flex gap-3 items-start rounded-xl border border-primary/40 bg-primary/5 p-3 cursor-pointer">
                <input type="radio" name="reservation-payment" checked={paymentMethod === "vnpay"} onChange={() => onPaymentMethodChange("vnpay")} className="mt-1 accent-primary" />
                <span><strong className="block text-sm">Cổng thanh toán VNPay</strong><span className="text-xs text-muted">Chọn ngân hàng hoặc phương thức QR tại bước thanh toán.</span></span>
              </label>
              {policy && (
                <div className="text-xs text-muted border-t border-black/8 pt-3 space-y-1">
                  <strong className="text-text">Điều kiện hoàn cọc</strong>
                  {policy.cancellationRules.map((rule) => (
                    <div key={rule.timeBucket} className="flex justify-between gap-3">
                      <span>{rule.timeBucket}</span><span>Hoàn {rule.refundPercentage}%</span>
                    </div>
                  ))}
                  {policy.cancellationRules.length === 0 && <p>{"Nhà hàng sẽ hướng dẫn khi bạn cần huỷ đặt chỗ."}</p>}
                </div>
              )}
            </section>
          )}

          <p className="text-sm text-muted px-1">Nhà hàng sẽ gọi điện xác nhận thông tin đặt chỗ của bạn.</p>
          <button type="submit" disabled={submitting} className="btn btn-primary w-full py-3.5! disabled:opacity-60">
            {submitting ? "Đang xử lý…" : foodItems.length > 0 ? "Thanh toán cọc & đặt chỗ" : "Xác nhận đặt chỗ"}
          </button>
        </aside>
      </form>
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return <div className="flex justify-between gap-4 text-sm"><span className="text-muted">{label}</span><span className="font-medium text-right">{value}</span></div>;
}
