import { useEffect } from "react";
import { Link } from "react-router-dom";
import SectionHeading from "@/components/ui/SectionHeading";
import FoodCard from "@/components/food/FoodCard";
import { useAsync } from "@/hooks/useAsync";
import { useAuthStore } from "@/store/authStore";
import { layGoiYMonAn, ghiSuKienGoiY } from "@/api/recommendations.api";

/**
 * "Gợi ý dành riêng cho bạn" — Top-N món từ AI (TF-IDF + Cosine) kèm lý do.
 * Khách mới / chưa đăng nhập nhận danh sách món phổ biến (cold-start).
 * Mỗi lần danh sách hiển thị và mỗi lần khách mở một món đều được ghi lại để đo CTR.
 */
export default function RecommendedSection() {
  const isAuthenticated = useAuthStore((s) => s.daDangNhap);
  const { data: goiY, loading } = useAsync(() => layGoiYMonAn(6), [isAuthenticated]);

  useEffect(() => {
    if (goiY?.length) ghiSuKienGoiY("hien_thi", "trang_chu", goiY);
  }, [goiY]);

  if (!loading && !goiY?.length) return null;

  const caNhan = goiY?.some((g) => !g.laKhoiDauLanh);

  return (
    <section className="py-24">
      <div className="max-w-290 mx-auto px-5 md:px-8">
        <SectionHeading align="center" title={caNhan ? "Gợi ý dành riêng cho bạn" : "Đang được yêu thích"}>
          {caNhan
            ? "Chọn theo khẩu vị từ những món bạn đã xem, thích và đặt."
            : isAuthenticated
              ? "Xem, thích hoặc đặt vài món, gợi ý sẽ dần hợp khẩu vị của bạn hơn."
              : (
                <>
                  Món được thực khách đánh giá cao.{" "}
                  <Link to="/dang-nhap" className="text-primary font-semibold hover:underline">Đăng nhập</Link>{" "}
                  để nhận gợi ý theo khẩu vị riêng.
                </>
              )}
        </SectionHeading>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {loading
            ? Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="rounded-card aspect-4/5 bg-black/5 animate-pulse" />
              ))
            : goiY!.map((g) => (
                <FoodCard
                  key={g.monAn.id}
                  food={g.monAn}
                  reason={g.laKhoiDauLanh ? undefined : g.lyDoGoiY}
                  onOpen={() => ghiSuKienGoiY("nhap", "trang_chu", [g])}
                />
              ))}
        </div>
      </div>
    </section>
  );
}
