import SectionHeading from "@/components/ui/SectionHeading";
import { useAsync } from "@/hooks/useAsync";
import { getPromotions } from "@/api/promotions.api";

export default function PromoPreviewSection() {
  const { data: promotions, loading } = useAsync(getPromotions);

  return (
    <section className="py-20">
      <div className="max-w-310 mx-auto px-5 md:px-8">
        <SectionHeading
          eyebrow="Khuyến mãi"
          title="Ưu đãi đang diễn ra"
          linkTo="/khuyen-mai"
        />
        {loading ? (
          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-5">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="rounded-[20px] h-47.5 bg-black/5 animate-pulse"
              />
            ))}
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-5">
            {promotions?.slice(0, 3).map((promo) => (
              <div
                key={promo.id}
                className="rounded-[20px] border-[1.5px] border-dashed border-primary/40 bg-linear-to-br from-white to-[#fbf1e8] p-6"
              >
                <div className="font-display text-[32px] text-primary mb-1.5">
                  {promo.discountLabel}
                </div>
                <h4 className="text-[15px] font-bold mb-4">{promo.title}</h4>
                <div className="flex items-center justify-between border-t border-dashed border-black/10 pt-3.5 text-xs">
                  <span className="text-muted">Mã ưu đãi</span>
                  <b className="tracking-wide">{promo.code}</b>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
