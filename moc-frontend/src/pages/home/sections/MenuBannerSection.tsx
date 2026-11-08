import { Link } from "react-router-dom";
import { HOME_IMAGES } from "../images";

export default function MenuBannerSection() {
  return (
    <section
      className="relative min-h-[50vh] md:min-h-[60vh] flex items-center justify-center overflow-hidden bg-[#140a0a] bg-cover bg-center md:bg-fixed"
      style={{ backgroundImage: `url(${HOME_IMAGES.banner})` }}
    >
      <div className="absolute inset-0 bg-black/55" />
      <div className="relative z-10 text-center text-white px-5 py-20">
        <h2 className="font-display text-white text-[36px] sm:text-[54px] leading-tight mb-4">
          Khám phá nghệ thuật ẩm thực
        </h2>
        <p className="text-white/80 text-[17px] sm:text-[19px] mb-9">
          Bản hoà tấu hương vị — chăm chút bằng đam mê và truyền thống.
        </p>
        <Link to="/thuc-don" className="btn btn-primary">
          Xem toàn bộ thực đơn
        </Link>
      </div>
    </section>
  );
}
