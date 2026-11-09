import { Link } from "react-router-dom";
import { Star } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getMyReviews } from "@/api/reviews.api";
import { formatDate } from "@/lib/utils";

export default function AccountReviewsPage() {
  const { data, loading, error } = useAsync(getMyReviews);

  return (
    <div>
      <h2 className="font-display text-xl mb-6">Đánh giá của tôi</h2>
      {loading ? (
        <div className="space-y-3">
          {[0, 1].map((i) => <div key={i} className="card h-24 animate-pulse bg-black/5" />)}
        </div>
      ) : error ? (
        <div className="card p-10 text-center text-sm text-muted">Không tải được đánh giá.</div>
      ) : !data?.length ? (
        <div className="card p-10 text-center">
          <Star width={30} height={30} className="mx-auto mb-3 text-muted" />
          <p className="text-muted text-sm">Bạn chưa đánh giá món ăn nào. Sau khi dùng bữa, hãy vào trang món để đánh giá.</p>
        </div>
      ) : (
        <ul className="space-y-3">
          {data.map((r) => (
            <li key={r.id} className="card p-5">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                <Link to={`/thuc-don/${r.idMonAn}`} className="font-semibold text-sm hover:text-primary">
                  {r.tenMonAn || `Món #${r.idMonAn}`}
                </Link>
                <span className="text-xs text-muted">{formatDate(r.taoLuc)}</span>
              </div>
              <div className="flex gap-0.5 mb-2" aria-label={`${r.diemDanhGia} trên 5 sao`}>
                {[1, 2, 3, 4, 5].map((n) => (
                  <Star key={n} width={15} height={15} className={n <= r.diemDanhGia ? "fill-amber-400 text-amber-400" : "text-black/20"} />
                ))}
              </div>
              {r.nhanXet && <p className="text-sm text-muted">{r.nhanXet}</p>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
