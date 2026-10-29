import { UtensilsCrossed, CalendarCheck, PenLine } from "lucide-react";
import type { ReservationOption } from "@/types";

const OPTIONS: {
  key: ReservationOption;
  icon: typeof UtensilsCrossed;
  title: string;
  desc: string;
  badge?: string;
}[] = [
  {
    key: "table_and_food",
    icon: UtensilsCrossed,
    title: "Đặt bàn + Gọi món trước",
    desc: "Món ăn được chuẩn bị sẵn trước giờ bạn đến — phù hợp cho nhóm đông hoặc dịp lễ. Cần đặt cọc trước.",
    badge: "Khuyên dùng",
  },
  {
    key: "table_only",
    icon: CalendarCheck,
    title: "Chỉ đặt bàn",
    desc: "Giữ chỗ trước, bạn gọi món trực tiếp khi đến nhà hàng như bình thường. Không cần đặt cọc.",
  },
  {
    key: "table_and_food_editable",
    icon: PenLine,
    title: "Đặt bàn + Chọn món (có thể đổi)",
    desc: "Chọn món trước để tiết kiệm thời gian, vẫn có thể thêm/bớt/đổi món tới trước giờ hẹn 2 tiếng. Cần đặt cọc.",
  },
];

export default function OptionStep({ onChoose }: { onChoose: (opt: ReservationOption) => void }) {
  return (
    <div>
      <h2 className="font-display text-2xl mb-2">Bạn muốn đặt theo hình thức nào?</h2>
      <p className="text-muted text-sm mb-8">
        Chọn "Gọi món trước" nếu bạn ghé vào giờ cao điểm hoặc dịp lễ — nhà hàng sẽ chuẩn bị món
        sẵn để bạn không phải chờ lâu.
      </p>
      <div className="grid md:grid-cols-3 gap-5">
        {OPTIONS.map((opt) => (
          <button
            key={opt.key}
            onClick={() => onChoose(opt.key)}
            className="text-left card p-6 hover:border-primary hover:shadow-lift transition-all relative"
          >
            {opt.badge && (
              <span className="absolute top-4 right-4 bg-primary text-white text-[10.5px] font-bold px-2.5 py-1 rounded-full">
                {opt.badge}
              </span>
            )}
            <div className="w-11 h-11 rounded-full bg-primary/10 text-primary flex items-center justify-center mb-4">
              <opt.icon width={20} height={20} />
            </div>
            <h3 className="font-display text-lg mb-2">{opt.title}</h3>
            <p className="text-[13px] text-muted leading-relaxed">{opt.desc}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
