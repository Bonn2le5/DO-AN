import { useEffect } from "react";
import { Plus, Sparkles, UtensilsCrossed } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { layGoiYMonAn, layMonTuongTu, ghiSuKienGoiY } from "@/api/recommendations.api";
import PlaceholderMedia from "@/components/ui/PlaceholderMedia";
import { formatCurrency } from "@/lib/utils";
import type { Food, Recommendation } from "@/types";

const SO_GOI_Y = 4;

/**
 * AI hỗ trợ gọi món ngay trong bước chọn món của đặt bàn:
 * - Chưa chọn món: Top-N theo khẩu vị (hoặc món phổ biến với khách mới).
 * - Đã chọn món: món tương tự / hợp với món vừa thêm (Item-to-Item TF-IDF).
 */
async function layGoiY(monVuaChon: Food | undefined, daChon: Set<string>): Promise<Recommendation[]> {
  const ds = monVuaChon
    ? await layMonTuongTu(monVuaChon.id, SO_GOI_Y + daChon.size)
    : await layGoiYMonAn(SO_GOI_Y + daChon.size);
  return ds.filter((g) => !daChon.has(g.food.id) && g.food.available).slice(0, SO_GOI_Y);
}

export default function FoodSuggestions({
  selectedFoods,
  onAdd,
}: {
  selectedFoods: Food[];
  onAdd: (food: Food) => void;
}) {
  const monVuaChon = selectedFoods[selectedFoods.length - 1];
  const daChon = new Set(selectedFoods.map((f) => f.id));
  const khoa = selectedFoods.map((f) => f.id).join(",");
  const { data: goiY, loading } = useAsync(() => layGoiY(monVuaChon, daChon), [khoa]);

  useEffect(() => {
    if (goiY?.length) ghiSuKienGoiY("hien_thi", "goi_mon", goiY);
  }, [goiY]);

  if (!loading && !goiY?.length) return null;

  const tieuDe = monVuaChon
    ? `Hợp với ${monVuaChon.name}`
    : goiY?.some((g) => !g.isColdStart) ? "Gợi ý theo khẩu vị của bạn" : "Món được gọi nhiều";

  return (
    <section aria-label="Gợi ý món" className="mb-6 rounded-2xl border border-primary/20 bg-primary/[0.03] p-4">
      <h3 className="flex items-center gap-1.5 text-sm font-semibold text-primary mb-3">
        <Sparkles size={15} aria-hidden="true" /> {tieuDe}
      </h3>
      <div className="flex gap-3 overflow-x-auto pb-1 -mx-1 px-1 [scrollbar-width:thin]">
        {loading
          ? Array.from({ length: SO_GOI_Y }).map((_, i) => (
              <div key={i} className="w-56 shrink-0 h-20 rounded-xl bg-black/5 animate-pulse" />
            ))
          : goiY!.map((g) => (
              <div key={g.food.id} className="w-64 shrink-0 flex gap-3 items-center bg-white rounded-xl border border-black/[0.07] p-2.5">
                {g.food.imageUrl ? (
                  <img src={g.food.imageUrl} alt="" className="w-14 h-14 rounded-lg object-cover bg-black/5 shrink-0" />
                ) : (
                  <PlaceholderMedia tone={g.food.placeholderTone} icon={UtensilsCrossed} className="w-14 h-14 rounded-lg shrink-0" iconClassName="w-5 h-5" />
                )}
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium leading-snug line-clamp-2">{g.food.name}</div>
                  {!g.isColdStart && g.reason && (
                    <div className="text-[11.5px] text-muted leading-snug line-clamp-2" title={g.reason}>{g.reason}</div>
                  )}
                  <div className="text-xs tabular-nums mt-0.5">{formatCurrency(g.food.price)}</div>
                </div>
                <button
                  type="button"
                  aria-label={`Thêm ${g.food.name}`}
                  onClick={() => {
                    ghiSuKienGoiY("nhap", "goi_mon", [g]);
                    onAdd(g.food);
                  }}
                  className="w-8 h-8 shrink-0 rounded-lg border border-primary/40 text-primary flex items-center justify-center hover:bg-primary hover:text-white transition-colors"
                >
                  <Plus size={15} />
                </button>
              </div>
            ))}
      </div>
    </section>
  );
}
