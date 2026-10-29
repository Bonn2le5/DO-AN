import { useAsync } from "@/hooks/useAsync";
import { getReviewsByFood } from "@/api/reviews.api";
import RatingStars from "@/components/ui/RatingStars";
import { formatDate } from "@/lib/utils";

export default function FoodReviews({ foodId }: { foodId: string }) {
  const { data: reviews, loading } = useAsync(() => getReviewsByFood(foodId), [foodId]);

  return (
    <div className="mt-20 max-w-2xl">
      <h2 className="font-display text-2xl mb-6">Đánh giá từ khách hàng</h2>
      {loading ? (
        <div className="space-y-4">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="h-24 rounded-2xl bg-black/[0.05] animate-pulse" />
          ))}
        </div>
      ) : !reviews || reviews.length === 0 ? (
        <p className="text-muted text-sm">Chưa có đánh giá cho món này.</p>
      ) : (
        <div className="space-y-5">
          {reviews.map((r) => (
            <div key={r.id} className="card p-5">
              <div className="flex items-center justify-between mb-2">
                <strong className="text-sm">{r.author}</strong>
                <span className="text-xs text-muted">{formatDate(r.createdAt)}</span>
              </div>
              <RatingStars rating={r.rating} size={13} className="mb-2" />
              <p className="text-sm text-muted leading-relaxed">{r.comment}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
