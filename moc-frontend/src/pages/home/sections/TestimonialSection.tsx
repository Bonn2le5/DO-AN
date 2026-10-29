import SectionHeading from "@/components/ui/SectionHeading";
import RatingStars from "@/components/ui/RatingStars";
import { cn } from "@/lib/utils";

const TESTIMONIALS = [
  {
    quote:
      "Đặt món qua web cực nhanh, phần gợi ý món ăn đúng gu tới bất ngờ. Đồ ăn giữ nhiệt tốt, đúng như hình.",
    name: "Lan Anh",
    role: "Khách hàng thân thiết",
    tone: "bg-primary",
  },
  {
    quote:
      "Không gian đẹp, đặt bàn online tiện lợi, nhân viên phản hồi chat rất nhanh khi mình hỏi về món ăn kiêng.",
    name: "Minh Tân",
    role: "Đặt bàn 2 lần/tháng",
    tone: "bg-accent",
  },
  {
    quote:
      "Combo cuối tuần rất đáng tiền, theo dõi trạng thái đơn hàng theo thời gian thực giúp mình yên tâm chờ.",
    name: "Hoài Thương",
    role: "Khách hàng mới",
    tone: "bg-secondary",
  },
];

export default function TestimonialSection() {
  return (
    <section className="py-20">
      <div className="max-w-310uto px-5 md:px-8">
        <SectionHeading eyebrow="Đánh giá" title="Khách hàng nói gì về MỘC" />
        <div className="grid md:grid-cols-3 gap-6">
          {TESTIMONIALS.map((t) => (
            <div key={t.name} className="card p-7">
              <RatingStars rating={5} size={14} className="mb-4" />
              <p className="text-[14.5px] leading-relaxed mb-5">"{t.quote}"</p>
              <div className="flex items-center gap-3">
                <div
                  className={cn(
                    "w-10.5 h-10.5 rounded-full flex items-center justify-center text-white font-display font-semibold",
                    t.tone,
                  )}
                >
                  {t.name.charAt(0)}
                </div>
                <div>
                  <strong className="block text-[13.5px]">{t.name}</strong>
                  <span className="text-[11.5px] text-muted">{t.role}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
