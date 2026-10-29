import { useNavigate, Link } from "react-router-dom";
import { useCartStore } from "@/store/cartStore";
import { createOrder } from "@/api/orders.api";
import CheckoutForm, { type CheckoutSubmitData } from "./CheckoutForm";
import OrderSummary from "./OrderSummary";

/**
 * CheckoutPage wires the cart store to CheckoutForm (contact/payment fields)
 * and OrderSummary (read-only cart recap). All field validation lives in
 * CheckoutForm; all order submission (API call) lives here.
 */
export default function CheckoutPage() {
  const navigate = useNavigate();
  const { items, subtotal, discount, total, appliedPromo, clearCart } =
    useCartStore();

  const handleSubmit = async (data: CheckoutSubmitData) => {
    const result = await createOrder({
      items,
      orderType: data.orderType,
      paymentMethod: data.paymentMethod,
      name: data.name,
      phone: data.phone,
      address: data.address,
      note: data.note,
      promoCode: appliedPromo?.code,
    });
    console.log("Order created:", result.orderId);
    clearCart();
    navigate("/don-hang/thanh-cong", { state: { orderId: result.orderId } });
  };

  if (items.length === 0) {
    return (
      <div className="max-w-lg mx-auto px-5 py-24 text-center">
        <h1 className="font-display text-2xl mb-3">
          Giỏ hàng của bạn đang trống
        </h1>
        <p className="text-muted mb-6">
          Hãy thêm món ăn trước khi tiến hành thanh toán.
        </p>
        <Link to="/thuc-don" className="btn btn-primary">
          Xem thực đơn
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-275 mx-auto px-5 md:px-8 py-12">
      <h1 className="font-display text-[32px] sm:text-[38px] mb-10">
        Thanh toán
      </h1>
      <div className="grid md:grid-cols-[1fr_400px] gap-12">
        <CheckoutForm total={total()} onSubmit={handleSubmit} />
        <OrderSummary
          items={items}
          subtotal={subtotal()}
          discount={discount()}
          total={total()}
          appliedPromo={appliedPromo}
        />
      </div>
    </div>
  );
}
