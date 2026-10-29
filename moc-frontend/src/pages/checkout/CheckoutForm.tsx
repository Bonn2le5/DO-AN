import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Truck, Store } from "lucide-react";
import { useState } from "react";
import { cn, formatCurrency } from "@/lib/utils";

export const checkoutSchema = z.object({
  name: z.string().min(2, "Vui lòng nhập họ tên"),
  phone: z.string().regex(/^(0|\+84)\d{9,10}$/, "Số điện thoại không hợp lệ"),
  address: z.string().optional(),
  note: z.string().optional(),
});
export type CheckoutFormData = z.infer<typeof checkoutSchema>;

export interface CheckoutSubmitData extends CheckoutFormData {
  orderType: "delivery" | "pickup";
  paymentMethod: "cod" | "bank";
}

interface CheckoutFormProps {
  total: number;
  onSubmit: (data: CheckoutSubmitData) => Promise<void>;
}

export default function CheckoutForm({ total, onSubmit }: CheckoutFormProps) {
  const [orderType, setOrderType] = useState<"delivery" | "pickup">("delivery");
  const [paymentMethod, setPaymentMethod] = useState<"cod" | "bank">("cod");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CheckoutFormData>({ resolver: zodResolver(checkoutSchema) });

  const submit = (data: CheckoutFormData) => onSubmit({ ...data, orderType, paymentMethod });

  return (
    <form onSubmit={handleSubmit(submit)} className="space-y-8">
      <div>
        <h2 className="text-sm font-bold uppercase tracking-wide text-muted mb-3.5">
          Hình thức nhận món
        </h2>
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => setOrderType("delivery")}
            className={cn(
              "flex items-center gap-3 px-4 py-3.5 rounded-xl border-[1.5px] transition-colors",
              orderType === "delivery" ? "border-primary bg-primary/5" : "border-black/15"
            )}
          >
            <Truck width={20} height={20} className={orderType === "delivery" ? "text-primary" : "text-muted"} />
            <span className="text-sm font-semibold">Giao tận nơi</span>
          </button>
          <button
            type="button"
            onClick={() => setOrderType("pickup")}
            className={cn(
              "flex items-center gap-3 px-4 py-3.5 rounded-xl border-[1.5px] transition-colors",
              orderType === "pickup" ? "border-primary bg-primary/5" : "border-black/15"
            )}
          >
            <Store width={20} height={20} className={orderType === "pickup" ? "text-primary" : "text-muted"} />
            <span className="text-sm font-semibold">Tự đến lấy</span>
          </button>
        </div>
      </div>

      <div>
        <h2 className="text-sm font-bold uppercase tracking-wide text-muted mb-3.5">
          Thông tin liên hệ
        </h2>
        <div className="space-y-4">
          <div>
            <input {...register("name")} placeholder="Họ và tên" className="w-full px-4 py-3.5 rounded-xl border border-black/15 text-sm outline-none focus:border-primary" />
            {errors.name && <p className="text-xs text-primary mt-1.5">{errors.name.message}</p>}
          </div>
          <div>
            <input {...register("phone")} placeholder="Số điện thoại" className="w-full px-4 py-3.5 rounded-xl border border-black/15 text-sm outline-none focus:border-primary" />
            {errors.phone && <p className="text-xs text-primary mt-1.5">{errors.phone.message}</p>}
          </div>
          {orderType === "delivery" && (
            <input {...register("address")} placeholder="Địa chỉ giao hàng" className="w-full px-4 py-3.5 rounded-xl border border-black/15 text-sm outline-none focus:border-primary" />
          )}
          <textarea
            {...register("note")}
            placeholder="Ghi chú cho đơn hàng (tuỳ chọn)"
            rows={3}
            className="w-full px-4 py-3.5 rounded-xl border border-black/15 text-sm outline-none focus:border-primary resize-none"
          />
        </div>
      </div>

      <div>
        <h2 className="text-sm font-bold uppercase tracking-wide text-muted mb-3.5">
          Phương thức thanh toán
        </h2>
        <div className="space-y-2.5">
          <label className={cn("flex items-center gap-3 px-4 py-3.5 rounded-xl border-[1.5px] cursor-pointer transition-colors", paymentMethod === "cod" ? "border-primary bg-primary/5" : "border-black/15")}>
            <input type="radio" checked={paymentMethod === "cod"} onChange={() => setPaymentMethod("cod")} className="accent-primary" />
            <span className="text-sm font-medium">Thanh toán khi nhận hàng (COD)</span>
          </label>
          <label className={cn("flex items-center gap-3 px-4 py-3.5 rounded-xl border-[1.5px] cursor-pointer transition-colors", paymentMethod === "bank" ? "border-primary bg-primary/5" : "border-black/15")}>
            <input type="radio" checked={paymentMethod === "bank"} onChange={() => setPaymentMethod("bank")} className="accent-primary" />
            <span className="text-sm font-medium">Chuyển khoản ngân hàng</span>
          </label>
        </div>
      </div>

      <button type="submit" disabled={isSubmitting} className="btn btn-primary w-full !py-4">
        {isSubmitting ? "Đang xử lý..." : `Đặt hàng · ${formatCurrency(total)}`}
      </button>
    </form>
  );
}
