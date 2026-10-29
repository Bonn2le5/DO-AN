import { Link } from "react-router-dom";
import { ArrowRight, ChefHat, Star } from "lucide-react";
import PlaceholderMedia from "@/components/ui/PlaceholderMedia";

export default function HeroSection() {
  return (
    <section className="pt-10 pb-20 md:pt-14 md:pb-24">
      <div className="max-w-310 mx-auto px-5 md:px-8 grid md:grid-cols-2 gap-14 items-center">
        <div>
          <div className="eyebrow">Nhà hàng Việt hiện đại</div>
          <h1 className="font-display text-[42px] sm:text-[56px] leading-[1.06] mb-6 max-w-140">
            Câu chuyện <em className="text-primary">ẩm thực</em> của chúng tôi
          </h1>
          <p className="text-[17px] text-muted max-w-110 mb-9 leading-relaxed">
            Nguyên liệu tươi mỗi ngày, công thức được chăm chút — mang tinh thần
            bếp Việt vào một trải nghiệm đặt món hiện đại, tinh tế.
          </p>
          <div className="flex gap-3.5 flex-wrap mb-14">
            <Link to="/thuc-don" className="btn btn-primary">
              Khám phá thực đơn <ArrowRight width={16} height={16} />
            </Link>
            <Link to="/dat-ban" className="btn btn-outline">
              Đặt bàn ngay
            </Link>
          </div>
          <div className="flex gap-10">
            <Stat value="12+" label="Năm phục vụ" />
            <Stat value="4.9" label="Đánh giá trung bình" />
            <Stat value="60k+" label="Món đã phục vụ" />
          </div>
        </div>

        <div className="relative h-100 md:h-140">
          <div className="absolute inset-0 rounded-[28px] overflow-hidden shadow-lift">
            <PlaceholderMedia
              tone={1}
              icon={ChefHat}
              className="w-full h-full"
              iconClassName="w-20 h-20"
            />
            <div className="absolute bottom-8 left-8 right-8 text-white">
              <div className="text-xs uppercase tracking-wider font-bold opacity-85">
                Món đặc trưng
              </div>
              <div className="font-display text-2xl mt-1.5">
                Bò lúc lắc sốt tiêu
              </div>
            </div>
          </div>
          <FloatCard
            className="top-6 -left-4 md:-left-8"
            icon={<ChefHat width={18} height={18} />}
            title="Đầu bếp 12 năm"
            subtitle="Kinh nghiệm bếp Việt"
          />
          <FloatCard
            className="bottom-10 -right-2 md:-right-6"
            icon={<Star width={18} height={18} />}
            title="4.9/5"
            subtitle="1,240 đánh giá"
          />
        </div>
      </div>
    </section>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <strong className="block font-display text-[26px]">{value}</strong>
      <span className="text-[12px] text-muted">{label}</span>
    </div>
  );
}

function FloatCard({
  className,
  icon,
  title,
  subtitle,
}: {
  className: string;
  icon: React.ReactNode;
  title: string;
  subtitle: string;
}) {
  return (
    <div
      className={`hidden sm:flex absolute bg-white rounded-2xl shadow-lift px-4.5 py-4 items-center gap-3 animate-bounce ${className}`}
      style={{ animationDuration: "5s" }}
    >
      <div className="w-9 h-9 rounded-full bg-bg flex items-center justify-center text-primary shrink-0">
        {icon}
      </div>
      <div>
        <strong className="block text-sm">{title}</strong>
        <span className="text-[11.5px] text-muted">{subtitle}</span>
      </div>
    </div>
  );
}
