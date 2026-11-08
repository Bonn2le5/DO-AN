import { useState, type FormEvent } from "react";
import { Star } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { createReview, getReviewsByFood } from "@/api/reviews.api";
import { useAuthStore } from "@/store/authStore";
import RatingStars from "@/components/ui/RatingStars";
import { formatDate } from "@/lib/utils";

export default function FoodReviews({ foodId }: { foodId: string }) {
  const { data: reviews, loading, refetch } = useAsync(() => getReviewsByFood(foodId), [foodId]);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setMessage(null);
    try {
      await createReview(foodId, rating, comment.trim());
      setComment("");
      setMessage({ ok: true, text: "Cảm ơn bạn đã đánh giá!" });
      refetch();
    } catch (err: any) {
      const d = err?.response?.data;
      const text = d?.mon_an ?? d?.detail ?? d?.non_field_errors ?? "Không gửi được đánh giá. Vui lòng thử lại.";
      setMessage({ ok: false, text: Array.isArray(text) ? text[0] : String(text) });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mt-20 max-w-2xl">
      <h2 className="font-display text-2xl mb-6">Đánh giá từ khách hàng</h2>
      {isAuthenticated && (
        <form onSubmit={submit} className="card p-5 mb-8 space-y-3">
          <div className="flex items-center gap-1" role="radiogroup" aria-label="Số sao">
            {[1, 2, 3, 4, 5].map((n) => (
              <button key={n} type="button" role="radio" aria-checked={rating === n} aria-label={`${n} sao`} onClick={() => setRating(n)}>
                <Star width={22} height={22} className={n <= rating ? "fill-accent stroke-accent" : "fill-none stroke-muted"} />
              </button>
            ))}
          </div>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Chia sẻ cảm nhận về món sau khi dùng tại nhà hàng…"
            aria-label="Nhận xét"
            rows={3}
            className="w-full px-4 py-3 rounded-xl border border-black/15 text-sm outline-none focus:border-primary resize-none"
          />
          {message && <p className={message.ok ? "text-sm text-success" : "text-sm text-primary"}>{message.text}</p>}
          <button type="submit" disabled={busy} className="btn btn-primary disabled:opacity-40">
            {busy ? "Đang gửi…" : "Gửi đánh giá"}
          </button>
        </form>
      )}
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
