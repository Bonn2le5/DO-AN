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

export default function ReservationPage() {
  const flow = useReservationFlow();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return (
      <div className="max-w-lg mx-auto px-5 py-24 text-center">
        <h1 className="font-display text-3xl mb-3">Đăng nhập để đặt bàn</h1>
        <p className="text-muted mb-7">Tài khoản giúp bạn theo dõi đặt chỗ và thanh toán cọc.</p>
        <Link to="/dang-nhap" state={{ from: "/dat-ban" }} className="btn btn-primary">Đăng nhập</Link>
      </div>
    );
  }

  const date = new Date(`${flow.date}T12:00:00`);
  const isWeekend = date.getDay() === 5 || date.getDay() === 6;
  const highPeak = isWeekend && flow.time >= "18:00" && flow.time < "21:00";

  return (
    <div className="max-w-275 mx-auto px-5 md:px-8 py-12">
      {flow.step !== "success" && (
        <>
          {(flow.step === "food" || flow.step === "contact") && !flow.reservation && (
            <button type="button" onClick={() => flow.setStep(flow.step === "food" ? "branch_time" : "food")} className="inline-flex items-center gap-1 text-sm font-semibold mb-5 hover:text-primary">
              <ChevronLeft size={18} /> Quay lại
            </button>
          )}
          <div className="mb-8">
            <div className="eyebrow">Đặt bàn</div>
            <h1 className="font-display text-[32px] sm:text-[38px]">Đặt bàn trước để không phải chờ</h1>
          </div>
          <ReservationStepper current={flow.step} />
        </>
      )}

      {flow.step === "branch_time" && (
        <BranchTimeStep
          selectedBranchId={flow.selectedBranchId}
          onBranchChange={flow.setSelectedBranchId}
          date={flow.date}
          onDateChange={flow.setDate}
          partySize={flow.partySize}
          onPartySizeChange={flow.setPartySize}
          selectedTime={flow.time}
          onTimeSelect={flow.setTime}
          tables={flow.tables}
          tablesLoading={flow.tablesLoading}
          selectedTableId={flow.selectedTableId}
          holdInfo={flow.holdInfo}
          holdLoading={flow.holdLoading}
          holdError={flow.holdError}
          onSelectTable={flow.selectTable}
          onContinue={() => flow.proceedFromBranchTime(flow.selectedBranchId, flow.selectedBranchName, flow.time)}
        />
      )}

      {flow.step === "food" && (
        <FoodStep
          foodItems={flow.foodItems}
          onAdd={flow.addFood}
          onUpdateQty={flow.updateFoodQty}
          subtotal={flow.foodSubtotal}
          depositAmount={flow.depositAmount}
          activeCategory={flow.foodCategory}
          onCategoryChange={flow.setFoodCategory}
          highPeak={highPeak}
          onContinue={flow.proceedToContact}
        />
      )}

      {flow.step === "contact" && flow.reservation && flow.reservation.depositAmount > 0 && (
        <PaymentStep
          reservation={flow.reservation}
          paymentSession={flow.paymentSession}
          error={flow.paymentError}
          retrying={flow.retryingPayment}
          onRetry={flow.retryPayment}
        />
      )}

      {flow.step === "contact" && !flow.reservation && (
        <ContactStep
          table={flow.selectedTable}
          date={flow.date}
          time={flow.time}
          partySize={flow.partySize}
          foodItems={flow.foodItems}
          foodSubtotal={flow.foodSubtotal}
          depositAmount={flow.depositAmount}
          depositPercentage={flow.policy?.depositPercentage ?? 20}
          policy={flow.policy}
          initialValues={flow.contact}
          paymentMethod={flow.paymentMethod}
          onPaymentMethodChange={flow.setPaymentMethod}
          onValuesChange={flow.updateContact}
          submitting={flow.submitting}
          onSubmit={flow.submitContact}
        />
      )}

      {flow.step === "success" && flow.reservation && (
        <ReservationSuccess reservation={flow.reservation} onReset={flow.reset} />
      )}
    </div>
  );
}
