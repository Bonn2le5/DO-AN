import { Link } from "react-router-dom";
import { HOME_IMAGES } from "../images";

export default function StorySection() {
  return (
    <section id="gioi-thieu" className="py-24 scroll-mt-20">
      <div className="max-w-310 mx-auto px-5 md:px-8 grid md:grid-cols-2 gap-14 lg:gap-20 items-center">
        <div className="relative">
          <img
            src={HOME_IMAGES.welcome}
            alt="Không gian nhà hàng MỘC"
            className="w-full aspect-4/5 object-cover rounded-2xl shadow-lift bg-black/10"
          />
          <img
            src={HOME_IMAGES.welcomeSmall}
            alt="Món ăn tại MỘC"
            className="hidden sm:block absolute -bottom-10 -right-8 w-[45%] aspect-square object-cover rounded-2xl border-8 border-bg shadow-lift bg-black/10"
          />
        </div>
        <div>
          <div className="text-[12.5px] font-bold uppercase tracking-[0.2em] text-primary mb-4">
            Câu chuyện của chúng tôi
          </div>
          <h2 className="font-display text-[34px] sm:text-[46px] leading-[1.12] mb-7">
            Chào mừng đến với MỘC — ẩm thực Việt nguyên bản
          </h2>
          <div className="space-y-5 text-muted text-[16px] leading-[1.85]">
            <p>
              MỘC bắt đầu từ một căn bếp nhỏ trong con hẻm Sài Gòn, nơi những
              công thức gia truyền được gìn giữ qua ba thế hệ. Mỗi món ăn đều
              được nấu từ nguyên liệu tươi chọn mỗi sáng.
            </p>
            <p>
              Hôm nay, chúng tôi mang tinh thần ấy vào một không gian ấm cúng,
              hiện đại — từ bữa trưa nhanh gọn đến bữa tối sum vầy cùng gia
              đình, kèm cả lựa chọn món chay cho mọi thực khách.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-6 my-9 border-y border-black/10 py-7">
            <Stat value="12+" label="Năm hoạt động" />
            <Stat value="45" label="Món trong thực đơn" />
            <Stat value="3" label="Chi nhánh" />
          </div>
          <Link to="/bai-viet" className="btn btn-primary">
            Đọc câu chuyện của chúng tôi
          </Link>
        </div>
      </div>
    </section>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <strong className="block font-display text-[34px] text-primary leading-none mb-2">
        {value}
      </strong>
      <span className="text-[13px] text-muted">{label}</span>
    </div>
  );
}
