import { useEffect } from "react";
import { useAsync } from "@/hooks/useAsync";
import { getRelatedFoods } from "@/api/foods.api";
import { layMonTuongTu, ghiSuKienGoiY } from "@/api/recommendations.api";
import FoodCard from "@/components/food/FoodCard";
import type { MonAn, GoiYMonAn } from "@/types";

/** Món tương tự theo AI (Item-to-Item TF-IDF); nếu API lỗi thì lấy món cùng danh mục. */
async function layDanhSach(food: MonAn): Promise<GoiYMonAn[]> {
  const ai = await layMonTuongTu(food.id, 3);
  if (ai.length) return ai;
  const cungDanhMuc = await getRelatedFoods(food);
  return cungDanhMuc.map((f) => ({ monAn: f, diemTuongDong: 0, lyDoGoiY: "" }));
}

export default function RelatedFoods({ food }: { food: MonAn }) {
  const { data: related, loading } = useAsync(() => layDanhSach(food), [food.id]);
  const tuAi = related?.some((r) => r.phienBanMoHinh);

  useEffect(() => {
    if (tuAi && related) ghiSuKienGoiY("hien_thi", "chi_tiet_mon", related);
  }, [related, tuAi]);

  if (!loading && (!related || related.length === 0)) return null;

  return (
    <div className="mt-20">
      <h2 className="font-display text-2xl mb-6">Món tương tự</h2>
      {loading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="rounded-card aspect-4/5 bg-black/5 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {related?.map((r) => (
            <FoodCard
              key={r.monAn.id}
              food={r.monAn}
              reason={r.lyDoGoiY || undefined}
              onOpen={tuAi ? () => ghiSuKienGoiY("nhap", "chi_tiet_mon", [r]) : undefined}
            />
          ))}
        </div>
      )}
    </div>
  );
}
