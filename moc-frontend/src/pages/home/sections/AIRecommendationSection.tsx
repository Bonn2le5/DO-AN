import { useState } from "react";
import { Link } from "react-router-dom";
import { Sparkles, UtensilsCrossed } from "lucide-react";
import PlaceholderMedia from "@/components/ui/PlaceholderMedia";
import { useAsync } from "@/hooks/useAsync";
import { getRecommendations } from "@/api/recommendations.api";
import { useAuthStore } from "@/store/authStore";
import { useCartStore } from "@/store/cartStore";
import { formatCurrency, cn } from "@/lib/utils";

export default function AIRecommendationSection() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const addItem = useCartStore((s) => s.addItem);
  // Demo toggle so reviewers can preview both auth states without logging in/out.
  // Real behaviour: just render based on `isAuthenticated` directly.
  const [previewLoggedIn, setPreviewLoggedIn] = useState(isAuthenticated);
  const { data: recommendations, loading } = useAsync(getRecommendations, [
    previewLoggedIn,
  ]);

  return (
    <section className="py-10">
      <div className="max-w-310 mx-auto px-3 sm:px-5 md:px-8">
        <div className="bg-dark rounded-4xl p-7 sm:p-12 md:p-16 text-white relative overflow-hidden">
          <div
            className="absolute w-130 h-130 rounded-full -top-56 -right-40 blur-2xl opacity-60"
            style={{
              background:
                "radial-gradient(circle, rgba(184,92,56,0.5), transparent 70%)",
            }}
          />
          <div className="relative flex items-center justify-between gap-6 flex-wrap mb-10">
            <div>
              <span className="inline-flex items-center gap-2 bg-white/8 border border-white/[0.14] px-4 py-2 rounded-full text-[12.5px] font-semibold mb-4">
                <Sparkles width={14} height={14} /> Đề xuất dành riêng cho bạn
              </span>
              <h2 className="font-display text-white text-[28px] sm:text-[34px] max-w-130">
                Dựa trên những món bạn yêu thích
              </h2>
              <p className="text-white/60 text-[14.5px] mt-2.5 max-w-110">
                Hệ thống AI học từ lịch sử đặt món, món đã xem và đánh giá của
                bạn để gợi ý chính xác hơn theo thời gian.
              </p>
            </div>
            <div className="flex gap-1 bg-white/8 p-1 rounded-full relative z-10">
              <button
                onClick={() => setPreviewLoggedIn(false)}
                className={cn(
                  "px-4.5 py-2.5 rounded-full text-[13px] font-semibold transition-colors",
                  !previewLoggedIn ? "bg-white text-dark" : "text-white/60",
                )}
              >
                Chưa đăng nhập
              </button>
              <button
                onClick={() => setPreviewLoggedIn(true)}
                className={cn(
                  "px-4.5 py-2.5 rounded-full text-[13px] font-semibold transition-colors",
                  previewLoggedIn ? "bg-white text-dark" : "text-white/60",
                )}
              >
                Đã đăng nhập
              </button>
            </div>
          </div>

          {!previewLoggedIn ? (
            <div className="relative z-10 text-center py-14 px-5 border-[1.5px] border-dashed border-white/20 rounded-[20px]">
              <Sparkles
                width={40}
                height={40}
                className="mx-auto mb-4 opacity-80"
              />
              <h3 className="font-display text-white text-xl mb-2.5">
                Đăng nhập để nhận gợi ý cá nhân hóa
              </h3>
              <p className="text-white/60 text-sm mb-6">
                Khám phá những món ăn được chọn riêng theo khẩu vị của bạn.
              </p>
              <Link to="/dang-nhap" className="btn btn-primary">
                Đăng nhập ngay
              </Link>
            </div>
          ) : loading ? (
            <div className="relative z-10 grid md:grid-cols-3 gap-5">
              {Array.from({ length: 3 }).map((_, i) => (
                <div
                  key={i}
                  className="h-70ded-[18px] bg-white/6 animate-pulse"
                />
              ))}
            </div>
          ) : (
            <div className="relative z-10 grid md:grid-cols-3 gap-5">
              {recommendations?.map((rec) => (
                <div
                  key={rec.food.id}
                  className="bg-white/6er border-white/10 rounded-card p-4.5 backdrop-blur-sm"
                >
                  <div className="aspect-4/3 rounded-xl overflow-hidden mb-3.5">
                    <PlaceholderMedia
                      tone={rec.food.placeholderTone}
                      icon={UtensilsCrossed}
                      className="w-full h-full"
                    />
                  </div>
                  <span className="inline-flex items-center gap-1.5 bg-accent/20 text-accent text-[11.5px] font-bold px-2.5 py-1 rounded-full mb-2.5">
                    {Math.round(rec.score * 100)}% phù hợp
                  </span>
                  <h4 className="font-display text-white text-lg mb-1.5">
                    {rec.food.name}
                  </h4>
                  <p className="text-white/55 text-[12.5px] leading-relaxed">
                    {rec.reason}
                  </p>
                  <button
                    onClick={() => addItem(rec.food)}
                    className="mt-3.5 w-full btn btn-primary py-2.5! text-[13px]!"
                  >
                    Thêm vào giỏ · {formatCurrency(rec.food.price)}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
