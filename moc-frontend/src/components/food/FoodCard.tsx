import { Link } from "react-router-dom";
import { Heart, Sparkles } from "lucide-react";
import type { MonAn } from "@/types";
import FoodImage from "@/components/food/FoodImage";
import RatingStars from "@/components/ui/RatingStars";
import { useFavoriteStore } from "@/store/favoriteStore";
import { formatCurrency, cn } from "@/lib/utils";

interface FoodCardProps {
  food: MonAn;
  /** Lý do gợi ý từ AI (Explainable Recommendation) — hiển thị dưới tên món. */
  reason?: string;
  /** Gọi khi khách mở món (dùng để ghi lượt nhấp vào gợi ý). */
  onOpen?: () => void;
}

export default function FoodCard({ food, reason, onOpen }: FoodCardProps) {
  const isFavorite = useFavoriteStore((s) => s.isFavorite(food.id));
  const toggleFavorite = useFavoriteStore((s) => s.toggle);

  return (
    <div className="card overflow-hidden group transition-all duration-400 hover:-translate-y-1.5 hover:shadow-lift">
      <Link
        to={`/thuc-don/${food.duongDan}`}
        onClick={onOpen}
        className="block relative aspect-4/3 overflow-hidden bg-black/5"
      >
        <FoodImage
          src={food.duongDanAnh}
          alt={food.tenMon}
          tone={food.phongCachHienThi}
          className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
        />
        {food.nhanHienThi && (
          <span className="absolute top-3 left-3 bg-dark text-white text-[11px] font-bold px-2.5 py-1 rounded-full">
            {food.nhanHienThi}
          </span>
        )}
        {!food.conHang && (
          <span className="absolute inset-0 bg-dark/55 flex items-center justify-center text-white text-sm font-semibold">
            Tạm hết hàng
          </span>
        )}
        <button
          onClick={(e) => {
            e.preventDefault();
            toggleFavorite(food.id);
          }}
          className="absolute top-2.5 right-2.5 w-8.5 h-8.5 rounded-full bg-white/90 flex items-center justify-center hover:scale-110 transition-transform"
        >
          <Heart
            width={16}
            height={16}
            className={cn(
              isFavorite ? "fill-primary stroke-primary" : "stroke-dark",
            )}
          />
        </button>
      </Link>
      <div className="p-5">
        <div className="text-[11.5px] uppercase tracking-wider text-muted font-bold">
          {food.tenDanhMuc}
        </div>
        <Link to={`/thuc-don/${food.duongDan}`} onClick={onOpen}>
          <h3 className="font-display text-xl mt-1.5 mb-1.5 hover:text-primary transition-colors">
            {food.tenMon}
          </h3>
        </Link>
        {reason ? (
          <p className="flex items-start gap-1.5 text-[13px] text-primary leading-snug mb-3.5 min-h-9.5">
            <Sparkles width={14} height={14} className="shrink-0 mt-0.5" aria-hidden="true" />
            <span className="line-clamp-2">{reason}</span>
          </p>
        ) : (
          <p className="text-[13.5px] text-muted leading-relaxed mb-3.5 min-h-9.5 line-clamp-2">
            {food.moTaNgan}
          </p>
        )}
        <div className="flex items-center gap-1.5 text-[12.5px] text-muted mb-3">
          <RatingStars rating={food.diemDanhGia} />
          <span>
            {food.diemDanhGia} · {food.soLuotDanhGia} đánh giá
          </span>
        </div>
        <span className="text-lg font-bold text-primary">
          {formatCurrency(food.donGia)}
        </span>
      </div>
    </div>
  );
}
