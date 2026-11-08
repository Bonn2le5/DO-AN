import { Leaf, ChefHat, Users, Clock } from "lucide-react";
import SectionHeading from "@/components/ui/SectionHeading";
import { HOME_IMAGES } from "../images";

const FEATURES = [
  { icon: Leaf, title: "Nguyên liệu tươi", text: "Rau, thịt, hải sản được chọn mỗi sáng từ chợ đầu mối và nông trại quen." },
  { icon: ChefHat, title: "Công thức gia truyền", text: "Những món ăn được nấu theo công thức truyền qua ba thế hệ trong gia đình." },
  { icon: Users, title: "Không gian ấm cúng", text: "Phù hợp cho bữa trưa văn phòng, hẹn hò hay tiệc sum họp gia đình." },
  { icon: Clock, title: "Đặt bàn & giao nhanh", text: "Đặt bàn online, theo dõi đơn hàng theo thời gian thực ngay trên web." },
];

export default function WhyChooseSection() {
  return (
    <section className="py-24 bg-[#efe7e3]/50 border-y border-black/5">
      <div className="max-w-310 mx-auto px-5 md:px-8">
        <SectionHeading align="center" eyebrow="Vì sao chọn MỘC" title="Trải nghiệm ẩm thực Việt trọn vẹn">
          Chúng tôi tin một bữa ăn ngon bắt đầu từ nguyên liệu tốt, được nấu
          bằng sự tận tâm và phục vụ bằng lòng hiếu khách.
        </SectionHeading>

        <div className="grid lg:grid-cols-[1fr_1.1fr] gap-10 items-stretch">
          <img
            src={HOME_IMAGES.why}
            alt="Bàn ăn tại MỘC"
            className="w-full h-full min-h-80 object-cover rounded-2xl shadow-lift bg-black/10"
          />
          <div className="grid sm:grid-cols-2 gap-5">
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <div
                key={title}
                className="bg-white rounded-2xl p-7 border border-black/6 hover:-translate-y-1 hover:shadow-lift transition-all duration-300"
              >
                <div className="w-13 h-13 rounded-xl bg-primary/10 text-primary flex items-center justify-center mb-5">
                  <Icon width={24} height={24} strokeWidth={1.6} />
                </div>
                <h3 className="font-display text-[21px] mb-2.5">{title}</h3>
                <p className="text-muted text-[14.5px] leading-relaxed">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
