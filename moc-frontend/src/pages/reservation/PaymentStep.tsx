import { ShieldCheck } from "lucide-react";
import HoldCountdown from "./HoldCountdown";
import ReservationTicket from "./ReservationTicket";
import { formatCurrency } from "@/lib/utils";
import type { VNPayPaymentSession, Reservation } from "@/types";

interface PaymentStepProps {
  reservation: Reservation;
  branchName: string;
  paymentSession: VNPayPaymentSession | null;
  error: string;
  retrying: boolean;
  onRetry: () => void;
}

export default function PaymentStep({
  reservation,
  branchName,
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

  const deposit = paymentSession?.amount || reservation.depositAmount;

  return (
    <div className="grid lg:grid-cols-[minmax(0,1fr)_minmax(0,420px)] gap-6 lg:gap-10 items-start">
      <div className="lg:order-2 space-y-5">
        <div>
          <h2 className="font-display text-[28px] sm:text-[32px] leading-tight">
            {paymentSession ? "Chỗ của bạn đang được giữ" : "Chưa mở được cổng thanh toán"}
          </h2>
          <p className="text-muted mt-2">
            {paymentSession
              ? "Thanh toán tiền cọc để hoàn tất đặt chỗ. Sau thời hạn dưới đây, chỗ giữ tạm sẽ được nhả cho khách khác."
              : `${error || "Chưa tạo được phiên thanh toán cọc."} Đặt chỗ #${reservation.id} vẫn được giữ, bạn có thể thử lại.`}
          </p>
        </div>

        <section className="bg-white rounded-[20px] border border-black/[0.07] p-5 sm:p-6">
          <div className="flex items-end justify-between gap-4">
            <div className="font-semibold">Tiền cọc</div>
            <div className="font-display text-[32px] leading-none text-primary tabular-nums">{formatCurrency(deposit)}</div>
          </div>
          {paymentSession && (
            <>
              <div className="flex justify-between gap-4 text-sm mt-3 pt-3 border-t border-black/8">
                <span className="text-muted">Mã giao dịch</span>
                <span className="tabular-nums break-all text-right">{paymentSession.txnRef}</span>
              </div>
              <div className="mt-4">
                <HoldCountdown until={paymentSession.expiresAt} label="Giữ chỗ còn" />
              </div>
            </>
          )}
        </section>

        {paymentSession ? (
          <>
            <button type="button" onClick={handleProceedPayment} className="btn btn-primary w-full">
              Thanh toán {formatCurrency(deposit)} qua VNPay
            </button>
            <p className="flex gap-2 text-sm text-muted">
              <ShieldCheck size={18} className="shrink-0" />
              Bạn sẽ được chuyển sang cổng VNPay (môi trường thử nghiệm) để chọn ngân hàng, thẻ hoặc quét QR.
            </p>
          </>
        ) : (
          <button type="button" onClick={onRetry} disabled={retrying} className="btn btn-primary w-full disabled:opacity-60">
            {retrying ? "Đang thử lại…" : "Thử mở cổng thanh toán lại"}
          </button>
        )}
      </div>

      <div className="lg:order-1">
        <ReservationTicket
          branchName={branchName}
          date={reservation.date}
          time={reservation.time}
          partySize={reservation.partySize}
          foodItems={reservation.foodItems ?? []}
          foodSubtotal={reservation.foodSubtotal}
          tableLabel={reservation.tableLabel}
          topLine={<>Mã đặt chỗ <strong className="text-text">#{reservation.id}</strong> · chờ thanh toán cọc</>}
        />
      </div>
    </div>
  );
}
