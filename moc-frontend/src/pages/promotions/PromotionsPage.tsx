import { useState } from "react";
import { Copy, Check } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getPromotions } from "@/api/promotions.api";
import { formatDate } from "@/lib/utils";

export default function PromotionsPage() {
  const { data: promotions, loading } = useAsync(getPromotions);
  const [copied, setCopied] = useState<string | null>(null);

  const handleCopy = (code: string) => {
    navigator.clipboard?.writeText(code).catch(() => {});
    setCopied(code);
    setTimeout(() => setCopied(null), 1800);
  };

  return (
    <div className="max-w-250 mx-auto px-5 md:px-8 py-12">
      <div className="mb-10">
        <div className="eyebrow">Khuyến mãi</div>
        <h1 className="font-display text-[32px] sm:text-[38px]">
          Ưu đãi đang diễn ra
        </h1>
        <p className="text-muted mt-2">
          Áp dụng mã ngay khi đặt món để nhận ưu đãi tốt nhất.
        </p>
      </div>

      {loading ? (
        <div className="grid sm:grid-cols-2 gap-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="rounded-[20px] h-52.5 bg-black/5 animate-pulse"
            />
          ))}
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 gap-6">
          {promotions?.map((promo) => (
            <div
              key={promo.id}
              className="rounded-[20px] border-[1.5px] border-dashed border-primary/40 bg-linear-to-br from-white to-[#fbf1e8] p-7"
            >
              <div className="font-display text-[36px] text-primary mb-2">
                {promo.discountLabel}
              </div>
              <h3 className="text-lg font-bold mb-2">{promo.title}</h3>
              <p className="text-sm text-muted mb-4">{promo.description}</p>
              {promo.minOrder && (
                <p className="text-xs text-muted mb-4">
                  Đơn tối thiểu: {promo.minOrder.toLocaleString("vi-VN")}đ
                </p>
              )}
              <div className="flex items-center justify-between border-t border-dashed border-black/15 pt-4">
                <div>
                  <div className="text-[11px] text-muted">
                    Hết hạn {formatDate(promo.expiresAt ?? promo.endsAt ?? "")}
                  </div>
                  <b className="tracking-wide text-sm">{promo.code}</b>
                </div>
                <button
                  onClick={() => handleCopy(promo.code)}
                  className="btn btn-outline py-2! px-4! text-[13px]!"
                >
                  {copied === promo.code ? (
                    <>
                      <Check width={14} height={14} /> Đã chép
                    </>
                  ) : (
                    <>
                      <Copy width={14} height={14} /> Sao chép
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
