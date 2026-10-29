import { Link } from "react-router-dom";
import { ChefHat, Salad } from "lucide-react";
import PlaceholderMedia from "@/components/ui/PlaceholderMedia";

export default function StorySection() {
  return (
    <section className="py-20">
      <div className="max-w-310 mx-auto px-5 md:px-8 grid md:grid-cols-2 gap-14 items-center">
        <div className="relative h-75 md:h-110">
          <div className="absolute top-0 left-0 w-[66%] h-[75%] rounded-[20px] overflow-hidden shadow-lift">
            <PlaceholderMedia
              tone={1}
              icon={ChefHat}
              className="w-full h-full"
            />
          </div>
          <div className="absolute bottom-0 right-0 w-[52%] h-[56%] rounded-[20px] overflow-hidden shadow-lift border-[6px] border-bg">
            <PlaceholderMedia tone={3} icon={Salad} className="w-full h-full" />
          </div>
        </div>
        <div>
          <div className="eyebrow">Câu chuyện của chúng tôi</div>
          <h2 className="font-display text-[32px] sm:text-[38px] leading-tight">
            Nấu bằng ký ức,
            <br />
            phục vụ bằng sự chăm chút
          </h2>
          <p className="text-muted text-[15.5px] leading-[1.85] my-6 max-w-120">
            MỘC bắt đầu từ một căn bếp nhỏ trong con hẻm Sài Gòn, nơi những công
            thức gia truyền được gìn giữ qua ba thế hệ. Hôm nay, chúng tôi mang
            tinh thần ấy vào một không gian hiện đại — vẫn giữ trọn vị nguyên
            bản, chỉ đổi cách bạn thưởng thức nó.
          </p>
          <Link to="/bai-viet" className="btn btn-outline">
            Tìm hiểu thêm
          </Link>
          <div className="flex gap-9 mt-8">
            <Stat value="12" label="Năm hoạt động" />
            <Stat value="45" label="Món trong thực đơn" />
            <Stat value="3" label="Chi nhánh" />
          </div>
        </div>
      </div>
    </section>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <strong className="block font-display text-[30px] text-primary">
        {value}
      </strong>
      <span className="text-[12px] text-muted">{label}</span>
    </div>
  );
}
