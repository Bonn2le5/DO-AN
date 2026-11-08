import { Link } from "react-router-dom";
import { Phone } from "lucide-react";

export default function CtaSection() {
  return (
    <section className="py-24 bg-primary text-white text-center">
      <div className="max-w-200 mx-auto px-5">
        <h2 className="font-display text-white text-[34px] sm:text-[48px] leading-tight mb-5">
          Sẵn sàng cho một bữa ăn trọn vị?
        </h2>
        <p className="text-white/80 text-[17px] leading-relaxed mb-10">
          Đặt bàn trước để có chỗ ngồi đẹp nhất, hoặc đặt món mang về — chúng
          tôi luôn sẵn sàng phục vụ bạn.
        </p>
        <div className="flex gap-4 justify-center flex-wrap">
          <Link to="/dat-ban" className="btn bg-white text-primary hover:bg-[#f8f5f1] hover:-translate-y-0.5">
            Đặt bàn ngay
          </Link>
          <Link to="/chi-nhanh" className="btn btn-light">
            <Phone width={16} height={16} /> Xem chi nhánh
          </Link>
        </div>
      </div>
    </section>
  );
}
