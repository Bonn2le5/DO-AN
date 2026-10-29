import { ShieldCheck } from "lucide-react";
import HoldCountdown from "./HoldCountdown";
import { formatCurrency } from "@/lib/utils";
import type { VNPayPaymentSession, Reservation } from "@/types";

interface PaymentStepProps {
  reservation: Reservation;
  paymentSession: VNPayPaymentSession | null;
  error: string;
  retrying: boolean;
  onRetry: () => void;
}

export default function PaymentStep({
  reservation,
  paymentSession,
  error,
  retrying,
  onRetry,
}: PaymentStepProps) {
  const handleProceedPayment = () => {
    if (paymentSession?.paymentUrl) {
      window.location.href = paymentSession.paymentUrl;
    }
  };

  if (!paymentSession) {
    return (
      <div className="max-w-md mx-auto text-center py-10">
        <h2 className="font-display text-2xl mb-2">Đặt bàn đã được ghi nhận</h2>
        <p className="text-muted text-sm mb-6">{error || "Chưa tạo được phiên đặt cọc."} Mã đặt bàn #{reservation.id} vẫn được giữ lại.</p>
        <button type="button" onClick={onRetry} disabled={retrying} className="btn btn-primary w-full py-3.5!">
          {retrying ? "Đang thử lại…" : "Thử tạo phiên thanh toán lại"}
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto text-center py-10">
      <div className="w-16 h-16 rounded-full bg-[#003a8f]/10 flex items-center justify-center mx-auto mb-6">
        <ShieldCheck width={30} height={30} className="text-[#003a8f]" />
      </div>
      <h2 className="font-display text-2xl mb-2">
        Thanh toán tiền cọc qua VNPay
      </h2>
      <p className="text-muted text-sm mb-6">
        Đơn <strong>#{reservation.id}</strong> — hoàn tất thanh toán để xác nhận
        giữ bàn.
      </p>

      <div className="card p-6 mb-6 text-left space-y-3">
        <div className="flex justify-between text-sm">
          <span className="text-muted">Mã giao dịch</span>
          <span className="font-mono">{paymentSession.txnRef}</span>
        </div>
        <div className="flex justify-between text-base font-bold pt-3 border-t border-black/8">
          <span>Số tiền cọc</span>
          <span className="text-primary">
            {formatCurrency(paymentSession.amount)}
          </span>
        </div>
      </div>

      <div className="mb-6">
        <HoldCountdown
          until={paymentSession.expiresAt}
          label="Hết hạn thanh toán sau"
        />
      </div>

      <div className="text-xs text-muted bg-[#003a8f]/5 text-[#003a8f] rounded-xl px-4 py-3 mb-6 leading-relaxed">
        Quý khách sẽ được chuyển hướng an toàn tới Cổng thanh toán VNPay Sandbox để hoàn tất đặt cọc.
      </div>

      <button
        type="button"
        onClick={handleProceedPayment}
        className="btn btn-primary w-full py-3.5! font-semibold"
      >
        Tiến hành thanh toán VNPay
      </button>
    </div>
  );
}

