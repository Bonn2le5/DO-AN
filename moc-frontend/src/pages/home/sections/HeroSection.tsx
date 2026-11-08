import { Link } from "react-router-dom";
import { ChevronDown } from "lucide-react";
import { HOME_IMAGES } from "../images";

export default function HeroSection() {
  return (
    <section className="relative min-h-[calc(100dvh-82px)] flex items-center justify-center overflow-hidden bg-[#140a0a]">
      <img
        src={HOME_IMAGES.hero}
        alt=""
        className="absolute inset-0 w-full h-full object-cover opacity-55 scale-105"
      />
      <div className="absolute inset-0 bg-linear-to-b from-black/50 via-black/30 to-black/70" />

      <div className="relative z-10 text-center text-white px-5 max-w-230 py-24">
        <div className="text-[12.5px] font-bold uppercase tracking-[0.3em] text-white/80 mb-6">
          Nhà hàng Việt · Since 2014
        </div>
        <h1 className="font-display text-white text-[44px] sm:text-[64px] md:text-[76px] leading-[1.08] mb-7">
          MỘC — Hương vị Việt
          <br className="hidden sm:block" /> giữa lòng Sài Gòn
        </h1>
        <p className="text-[17px] sm:text-[20px] text-white/85 max-w-150 mx-auto mb-11 leading-relaxed">
          Món ngon truyền thống từ nguyên liệu tươi mỗi ngày, phục vụ trong
          không gian ấm cúng cho gia đình và bạn bè.
        </p>
        <div className="flex gap-4 justify-center flex-wrap">
          <Link to="/dat-ban" className="btn btn-primary">
            Đặt bàn ngay
          </Link>
          <Link to="/thuc-don" className="btn btn-light">
            Xem thực đơn
          </Link>
        </div>
      </div>

      <a
        href="#gioi-thieu"
        aria-label="Cuộn xuống"
        className="absolute bottom-8 left-1/2 -translate-x-1/2 text-white/70 hover:text-white animate-bounce"
      >
        <ChevronDown width={30} height={30} />
      </a>
    </section>
  );
}
