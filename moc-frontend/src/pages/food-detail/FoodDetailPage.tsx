import { Link, useParams } from "react-router-dom";
import { ChevronRight, UtensilsCrossed } from "lucide-react";
import PlaceholderMedia from "@/components/ui/PlaceholderMedia";
import { useAsync } from "@/hooks/useAsync";
import { getFoodBySlug } from "@/api/foods.api";
import FoodPurchasePanel from "./FoodPurchasePanel";
import FoodReviews from "./FoodReviews";
import RelatedFoods from "./RelatedFoods";
import NotFoundPage from "@/pages/NotFoundPage";

/**
 * FoodDetailPage only handles: fetching the food by slug, breadcrumb, and
 * the image column. Purchase logic (FoodPurchasePanel), reviews
 * (FoodReviews), and related items (RelatedFoods) are separate files that
 * each own their own state/data — this file stays readable as the app grows.
 */
export default function FoodDetailPage() {
  const { slug } = useParams();
  const { data: food, loading } = useAsync(() => getFoodBySlug(slug!), [slug]);

  if (loading) {
    return (
      <div className="max-w-310 mx-auto px-5 md:px-8 py-10 grid md:grid-cols-2 gap-12">
        <div className="aspect-square rounded-3xl bg-black/5 animate-pulse" />
        <div className="space-y-4">
          <div className="h-8 w-2/3 bg-black/5 rounded animate-pulse" />
          <div className="h-4 w-full bg-black/5 rounded animate-pulse" />
          <div className="h-4 w-5/6 bg-black/5 rounded animate-pulse" />
        </div>
      </div>
    );
  }

  if (!food) return <NotFoundPage />;

  return (
    <div className="max-w-310 mx-auto px-5 md:px-8 py-10">
      <div className="flex items-center gap-1.5 text-[13px] text-muted mb-8">
        <Link to="/" className="hover:text-primary">
          Trang chủ
        </Link>
        <ChevronRight width={13} height={13} />
        <Link to="/thuc-don" className="hover:text-primary">
          Thực đơn
        </Link>
        <ChevronRight width={13} height={13} />
        <span className="text-text">{food.name}</span>
      </div>

      <div className="grid md:grid-cols-2 gap-12">
        <div className="rounded-3xl overflow-hidden aspect-square sticky top-24 self-start">
          <PlaceholderMedia
            tone={food.placeholderTone}
            icon={UtensilsCrossed}
            className="w-full h-full"
            iconClassName="w-24 h-24"
          />
        </div>
        <FoodPurchasePanel food={food} />
      </div>

      <FoodReviews foodId={food.id} />
      <RelatedFoods food={food} />
    </div>
  );
}
