import { Plus, UtensilsCrossed } from "lucide-react";
import SectionHeading from "@/components/ui/SectionHeading";
import PlaceholderMedia from "@/components/ui/PlaceholderMedia";
import { useAsync } from "@/hooks/useAsync";
import { getCombos } from "@/api/foods.api";
import { formatCurrency } from "@/lib/utils";

export default function ComboSection() {
  const { data: combos, loading } = useAsync(getCombos);

  return (
    <section className="py-20">
      <div className="max-w-310 mx-auto px-5 md:px-8">
        <SectionHeading
          eyebrow="Ưu đãi combo"
          title="Combo tiết kiệm hôm nay"
        />
        {loading ? (
          <div className="grid md:grid-cols-3 gap-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="rounded-[22px] min-h-80 bg-black/5 animate-pulse"
              />
            ))}
          </div>
        ) : (
          <div className="grid md:grid-cols-3 gap-6">
            {combos?.map((combo) => (
              <div
                key={combo.id}
                className="relative rounded-[22px] overflow-hidden min-h-80 flex flex-col justify-end p-6 text-white"
              >
                <PlaceholderMedia
                  tone={combo.placeholderTone}
                  icon={UtensilsCrossed}
                  className="absolute inset-0 w-full h-full"
                />
                <div className="absolute inset-0 bg-linear-to-t from-black/75 via-black/10 to-transparent" />
                <div className="relative z-10">
                  <span className="inline-block bg-success text-[11.5px] font-bold px-3 py-1 rounded-full mb-2.5">
                    Tiết kiệm {formatCurrency(combo.oldPrice - combo.price)}
                  </span>
                  <h3 className="font-display text-2xl mb-1.5">{combo.name}</h3>
                  <p className="text-[12.5px] opacity-80 mb-3.5">
                    {combo.items.join(" · ")}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-xl font-bold">
                      {formatCurrency(combo.price)}{" "}
                      <span className="text-[13px] line-through opacity-55 font-normal">
                        {formatCurrency(combo.oldPrice)}
                      </span>
                    </span>
                    <button className="w-10 h-10 rounded-full bg-white/20 hover:bg-primary flex items-center justify-center transition-colors">
                      <Plus width={17} height={17} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
