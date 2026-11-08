import { Link } from "react-router-dom";
import { ArrowRight, Star } from "lucide-react";
import type { Food } from "@/types";
import SectionHeading from "@/components/ui/SectionHeading";
import FoodImage from "@/components/food/FoodImage";
import { useAsync } from "@/hooks/useAsync";
import { layDanhSachMonAn } from "@/api/foods.api";
import { foods as mockFoods } from "@/data/mock";
import { formatCurrency } from "@/lib/utils";

/** Lấy ngẫu nhiên 9 món đang bán (dùng dữ liệu mẫu nếu API chưa có món). */
async function getRandomFoods(): Promise<Food[]> {
  const fromApi = await layDanhSachMonAn();
  const pool = (fromApi.length ? fromApi : mockFoods).filter((f) => f.available);
  const shuffled = [...pool].sort(() => Math.random() - 0.5);
  // Ưu tiên món có ảnh; chỉ dùng món chưa có ảnh khi không đủ 9 món.
  const withImage = shuffled.filter((f) => f.imageUrl);
  const noImage = shuffled.filter((f) => !f.imageUrl);
  return [...withImage, ...noImage].slice(0, 9);
}

export default function BestSellerSection() {
  const { data: foods, loading } = useAsync(getRandomFoods);

  return (
    <section className="py-24 bg-[#efe7e3]/40 border-y border-black/5">
      <div className="max-w-290 mx-auto px-5 md:px-8">
        <SectionHeading align="center" title="Món bán chạy của chúng tôi">
          Những món thực khách yêu thích nhất — lựa chọn hoàn hảo cho lần đầu
          ghé MỘC.
        </SectionHeading>

        <div className="flex flex-wrap justify-center gap-8">
          {loading
            ? Array.from({ length: 9 }).map((_, i) => (
                <div key={i} className={`${CARD_W} h-115 rounded-xl bg-black/5 animate-pulse`} />
              ))
            : foods?.map((food) => <BestSellerCard key={food.id} food={food} />)}
        </div>

        <div className="text-center mt-14">
          <Link to="/thuc-don" className="btn btn-primary rounded-full!">
            Khám phá toàn bộ thực đơn <ArrowRight width={16} height={16} />
          </Link>
        </div>
      </div>
    </section>
  );
}

const CARD_W = "w-full sm:w-[calc(50%-1rem)] lg:w-[calc(33.333%-1.34rem)]";

function BestSellerCard({ food }: { food: Food }) {
  return (
    <Link
      to={`/thuc-don/${food.slug}`}
      className={`${CARD_W} group bg-white rounded-xl overflow-hidden border border-black/8 shadow-[0_2px_10px_rgba(60,20,20,0.06)] hover:-translate-y-1.5 hover:shadow-lift transition-all duration-300`}
    >
      <div className="relative aspect-4/3 overflow-hidden bg-black/5">
        <FoodImage
          src={food.imageUrl}
          alt={food.name}
          tone={food.placeholderTone}
          className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
          iconClassName="w-14 h-14"
        />
        <span className="absolute top-4 right-4 inline-flex items-center gap-1 bg-gold text-wine-dark text-[12px] font-bold uppercase tracking-wider px-3 py-1 rounded-full shadow">
          <Star width={11} height={11} className="fill-current" /> Bán chạy
        </span>
      </div>
      <div className="p-6">
        <div className="flex items-start justify-between gap-4 mb-3">
          <h3 className="font-serif text-[20px] font-bold leading-snug line-clamp-2 group-hover:text-primary transition-colors">
            {food.name}
          </h3>
          <span className="shrink-0 font-semibold text-[15px] pt-1">
            {formatCurrency(food.price)}
          </span>
        </div>
        <p className="text-muted text-[14.5px] leading-relaxed line-clamp-2">
          {food.description}
        </p>
      </div>
    </Link>
  );
}
