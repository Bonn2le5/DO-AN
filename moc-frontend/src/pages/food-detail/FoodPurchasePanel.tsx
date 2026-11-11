import { Heart, Flame, Leaf } from "lucide-react";
import RatingStars from "@/components/ui/RatingStars";
import { useFavoriteStore } from "@/store/favoriteStore";
import { formatCurrency, cn } from "@/lib/utils";
import type { MonAn } from "@/types";

export default function FoodPurchasePanel({ food }: { food: MonAn }) {
  const isFavorite = useFavoriteStore((s) => s.isFavorite(food.id));
  const toggleFavorite = useFavoriteStore((s) => s.toggle);

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[12.5px] font-bold uppercase tracking-wide text-primary">
          {food.tenDanhMuc}
        </span>
        {food.nhanHienThi && (
          <span className="bg-dark text-white text-[11px] font-bold px-2.5 py-1 rounded-full">
            {food.nhanHienThi}
          </span>
        )}
      </div>
      <h1 className="font-display text-[32px] sm:text-[38px] mb-3">
        {food.tenMon}
      </h1>

      <div className="flex items-center gap-2.5 mb-5">
        <RatingStars rating={food.diemDanhGia} size={15} />
        <span className="text-sm text-muted">
          {food.diemDanhGia} · {food.soLuotDanhGia} đánh giá
        </span>
      </div>

      <p className="text-[15px] text-muted leading-relaxed mb-6">
        {food.moTaChiTiet}
      </p>

      <div className="flex flex-wrap gap-2 mb-6">
        {food.laMonChay && (
          <span className="inline-flex items-center gap-1.5 bg-success/10 text-success text-xs font-semibold px-3 py-1.5 rounded-full">
            <Leaf width={13} height={13} /> Món chay
          </span>
        )}
        {food.doCay > 0 && (
          <span className="inline-flex items-center gap-1.5 bg-primary/10 text-primary text-xs font-semibold px-3 py-1.5 rounded-full">
            <Flame width={13} height={13} /> Độ cay {food.doCay}/3
          </span>
        )}
        {food.theMonAn.map((tag) => (
          <span
            key={tag}
            className="bg-black/5 text-xs font-medium px-3 py-1.5 rounded-full"
          >
            {tag}
          </span>
        ))}
      </div>

      {food.nguyenLieu.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-bold uppercase tracking-wide text-muted mb-2.5">
            Nguyên liệu chính
          </h3>
          <p className="text-sm text-text">{food.nguyenLieu.join(", ")}</p>
        </div>
      )}

      <div className="border-t border-black/8 pt-6">
        <div className="flex items-baseline justify-between mb-5">
          <span className="font-display text-3xl text-primary">
            {formatCurrency(food.donGia)}
          </span>
          {!food.conHang ? (
            <span className="text-sm font-semibold text-primary">
              Tạm hết hàng
            </span>
          ) : (
            <span className="text-sm text-muted">
              Còn {food.tonKho} phần hôm nay
            </span>
          )}
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={() => toggleFavorite(food.id)}
            className="w-13 h-13 rounded-full border border-black/15 flex items-center justify-center shrink-0 hover:bg-black/5"
          >
            <Heart
              width={19}
              height={19}
              className={cn(
                isFavorite ? "fill-primary stroke-primary" : "stroke-dark",
              )}
            />
          </button>
        </div>
      </div>
    </div>
  );
}
