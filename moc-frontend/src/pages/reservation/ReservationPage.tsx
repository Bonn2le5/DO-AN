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
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  // Mỗi lần đổi bước, đưa người dùng về đầu trang.
  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [flow.step]);

  if (!isAuthenticated) {
    return (
      <div className="reservation-ui max-w-lg mx-auto px-5 py-24 text-center">
        <h1 className="font-display text-3xl mb-3">Đăng nhập để đặt bàn</h1>
        <p className="text-muted mb-7">Tài khoản giúp bạn theo dõi đặt chỗ và thanh toán cọc.</p>
        <Link to="/dang-nhap" state={{ from: "/dat-ban" }} className="btn btn-primary">Đăng nhập</Link>
      </div>
    );
  }

  if (flow.step === "success" && flow.reservation) {
    return <ReservationSuccess reservation={flow.reservation} branchName={flow.selectedBranchName} onReset={flow.reset} />;
  }

  const date = new Date(`${flow.date}T12:00:00`);
  const isWeekend = date.getDay() === 5 || date.getDay() === 6;
  const highPeak = isWeekend && flow.time >= "18:00" && flow.time < "21:00";
  const canGoBack = (flow.step === "food" || flow.step === "contact") && !flow.reservation;
  const step = flow.step === "success" ? "contact" : flow.step;
  // Bước xác nhận (form) phải vừa một màn hình nên thu gọn phần đầu trang.
  const compact = flow.step === "contact" && !flow.reservation;

  return (
    <div className={`reservation-ui max-w-275 mx-auto px-4 sm:px-5 md:px-8 ${compact ? "pt-4 lg:pt-6 pb-10" : "pt-8 sm:pt-12 pb-16"}`}>
      {canGoBack && (
        <button
          type="button"
          onClick={() => flow.setStep(flow.step === "food" ? "branch_time" : "food")}
          className={`items-center gap-1 text-sm font-semibold text-muted hover:text-primary ${compact ? "hidden lg:inline-flex mb-1" : "inline-flex mb-4"}`}
        >
          <ChevronLeft size={18} /> {flow.step === "food" ? "Đổi giờ hẹn" : "Sửa món"}
        </button>
      )}

      <h1 className={`font-display leading-tight ${compact ? "max-lg:sr-only text-[28px] mb-3" : "text-[30px] sm:text-[40px] mb-6"}`}>{HEADINGS[step]}</h1>
      <ReservationStepper current={flow.step} compact={compact} />

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
          onContinue={flow.proceedFromBranchTime}
        />
      )}

      {flow.step === "food" && (
        <FoodStep
          foodItems={flow.foodItems}
          onAdd={flow.addFood}
          onUpdateQty={flow.updateFoodQty}
          subtotal={flow.foodSubtotal}
          depositAmount={flow.depositAmount}
          depositPercentage={flow.policy?.depositPercentage ?? 20}
          activeCategory={flow.foodCategory}
          onCategoryChange={flow.setFoodCategory}
          highPeak={highPeak}
          time={flow.time}
          date={flow.date}
          partySize={flow.partySize}
          branchName={flow.selectedBranchName}
          onContinue={flow.proceedToContact}
        />
      )}

      {flow.step === "contact" && flow.reservation && flow.reservation.depositAmount > 0 && (
        <PaymentStep
          reservation={flow.reservation}
          branchName={flow.selectedBranchName}
          paymentSession={flow.paymentSession}
          error={flow.paymentError}
          retrying={flow.retryingPayment}
          onRetry={flow.retryPayment}
        />
      )}

      {flow.step === "contact" && !flow.reservation && (
        <ContactStep
          branchName={flow.selectedBranchName}
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
          onEditTime={() => flow.setStep("branch_time")}
          onEditFood={() => flow.setStep("food")}
        />
      )}
    </div>
  );
}
