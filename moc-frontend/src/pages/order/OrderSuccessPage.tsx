import { useLocation, Link } from "react-router-dom";
import { CheckCircle2 } from "lucide-react";
import OrderTrackingCard from "@/components/order/OrderTrackingCard";

export default function OrderSuccessPage() {
  const location = useLocation();
  const orderId = location.state?.orderId;

  return (
    <div className="max-w-2xl mx-auto px-5 py-16 text-center">
      <div className="w-20 h-20 rounded-full bg-success/10 flex items-center justify-center mx-auto mb-6">
        <CheckCircle2 width={40} height={40} className="text-success" />
      </div>
      <h1 className="font-display text-3xl mb-3">Đặt hàng thành công!</h1>
      {orderId ? (
        <div className="text-left my-8">
          <OrderTrackingCard orderIdOrCode={orderId} />
        </div>
      ) : (
        <p className="text-muted mb-8 text-sm">
          Nhà hàng sẽ liên hệ để xác nhận đơn hàng trong ít phút. Bạn có thể theo dõi trạng thái đơn
          hàng theo thời gian thực trong trang Tài khoản.
        </p>
      )}
      <div className="flex gap-3 justify-center flex-wrap">
        <Link to="/thuc-don" className="btn btn-outline">Tiếp tục đặt món</Link>
        <Link to="/tai-khoan/don-hang" className="btn btn-primary">Theo dõi đơn hàng</Link>
      </div>
    </div>
  );
}
