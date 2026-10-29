import { useEffect, useState, useMemo } from "react";
import { Star, Eye, EyeOff, Trash2, Search, RefreshCw } from "lucide-react";
import { getAdminReviews, toggleReviewVisibility, deleteAdminReview, type AdminReviewItem } from "@/api/admin.api";

export default function AdminReviewsPage() {
  const [reviews, setReviews] = useState<AdminReviewItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [ratingFilter, setRatingFilter] = useState("all");
  const [visibilityFilter, setVisibilityFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchReviews = async () => {
    setLoading(true);
    try {
      const data = await getAdminReviews();
      setReviews(data);
    } catch (err) {
      console.error("Failed to load reviews:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, []);

  const handleToggle = async (review: AdminReviewItem) => {
    try {
      await toggleReviewVisibility(review.id, !review.hien_thi);
      fetchReviews();
    } catch (err) {
      alert("Không thể thay đổi trạng thái đánh giá.");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Bạn có chắc chắn muốn xóa vĩnh viễn đánh giá này?")) return;
    try {
      await deleteAdminReview(id);
      fetchReviews();
    } catch (err) {
      alert("Không thể xóa đánh giá.");
    }
  };

  const filteredReviews = useMemo(() => {
    return reviews.filter((r) => {
      const matchRating = ratingFilter === "all" || String(r.diem_danh_gia) === ratingFilter;
      const matchVis =
        visibilityFilter === "all" ||
        (visibilityFilter === "visible" && r.hien_thi) ||
        (visibilityFilter === "hidden" && !r.hien_thi);
      const matchSearch =
        !searchQuery ||
        r.ten_nguoi_dung?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.nhan_xet?.toLowerCase().includes(searchQuery.toLowerCase());
      return matchRating && matchVis && matchSearch;
    });
  }, [reviews, ratingFilter, visibilityFilter, searchQuery]);

  const avgRating = useMemo(() => {
    if (reviews.length === 0) return 0;
    const sum = reviews.reduce((acc, r) => acc + Number(r.diem_danh_gia), 0);
    return (sum / reviews.length).toFixed(1);
  }, [reviews]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Quản lý & Duyệt đánh giá</h1>
          <p className="text-sm text-gray-500">Kiểm duyệt ý kiến phản hồi của khách hàng đối với các món ăn.</p>
        </div>
        <button onClick={fetchReviews} className="p-2 border rounded-lg hover:bg-gray-100" title="Làm mới">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-xl border shadow-sm">
          <div className="text-sm text-gray-500 font-medium">Tổng số phản hồi</div>
          <div className="text-3xl font-bold text-gray-900 mt-1">{reviews.length}</div>
        </div>
        <div className="bg-white p-5 rounded-xl border shadow-sm">
          <div className="text-sm text-gray-500 font-medium">Điểm đánh giá trung bình</div>
          <div className="text-3xl font-bold text-amber-500 mt-1 flex items-center gap-2">
            ⭐ {avgRating} / 5.0
          </div>
        </div>
        <div className="bg-white p-5 rounded-xl border shadow-sm">
          <div className="text-sm text-gray-500 font-medium">Đang hiển thị công khai</div>
          <div className="text-3xl font-bold text-emerald-600 mt-1">
            {reviews.filter((r) => r.hien_thi).length}
          </div>
        </div>
      </div>

      {/* Reviews Table */}
      <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
        {/* Filters Bar */}
        <div className="p-4 border-b flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
            <input
              type="text"
              placeholder="Tìm theo tên khách hàng hoặc nội dung nhận xét..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={ratingFilter}
              onChange={(e) => setRatingFilter(e.target.value)}
              className="px-3 py-2 border rounded-lg text-sm bg-white"
            >
              <option value="all">Tất cả số sao</option>
              <option value="5">5 Sao ⭐⭐⭐⭐⭐</option>
              <option value="4">4 Sao ⭐⭐⭐⭐</option>
              <option value="3">3 Sao ⭐⭐⭐</option>
              <option value="2">2 Sao ⭐⭐</option>
              <option value="1">1 Sao ⭐</option>
            </select>
            <select
              value={visibilityFilter}
              onChange={(e) => setVisibilityFilter(e.target.value)}
              className="px-3 py-2 border rounded-lg text-sm bg-white"
            >
              <option value="all">Tất cả trạng thái</option>
              <option value="visible">Đang hiển thị</option>
              <option value="hidden">Đã ẩn</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center text-gray-500">Đang tải danh sách đánh giá...</div>
        ) : filteredReviews.length === 0 ? (
          <div className="p-12 text-center text-gray-400">Không có đánh giá nào thỏa mãn bộ lọc.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 border-b text-gray-600 font-medium">
                <tr>
                  <th className="p-3.5">Khách hàng</th>
                  <th className="p-3.5">Món ăn / Đơn</th>
                  <th className="p-3.5">Đánh giá</th>
                  <th className="p-3.5">Nhận xét</th>
                  <th className="p-3.5">Thời gian</th>
                  <th className="p-3.5">Trạng thái</th>
                  <th className="p-3.5 text-right">Hành động</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredReviews.map((r) => (
                  <tr key={r.id} className="hover:bg-gray-50/70 transition-colors">
                    <td className="p-3.5 font-semibold text-gray-900">{r.ten_nguoi_dung || "Khách hàng"}</td>
                    <td className="p-3.5 text-gray-600">
                      <div>Món #{r.mon_an}</div>
                      <div className="text-xs text-gray-400">Đơn #{r.don_hang}</div>
                    </td>
                    <td className="p-3.5">
                      <div className="flex text-amber-400">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <Star
                            key={i}
                            className={`w-4 h-4 ${i < r.diem_danh_gia ? "fill-amber-400" : "text-gray-300"}`}
                          />
                        ))}
                      </div>
                    </td>
                    <td className="p-3.5 text-gray-800 max-w-xs">{r.nhan_xet || <span className="italic text-gray-400">Không có lời bình</span>}</td>
                    <td className="p-3.5 text-xs text-gray-500">{new Date(r.tao_luc).toLocaleDateString("vi-VN")}</td>
                    <td className="p-3.5">
                      <span
                        className={`px-2.5 py-1 text-xs rounded-full font-medium ${
                          r.hien_thi ? "bg-emerald-100 text-emerald-800" : "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {r.hien_thi ? "Công khai" : "Đã ẩn"}
                      </span>
                    </td>
                    <td className="p-3.5 text-right space-x-1">
                      <button
                        onClick={() => handleToggle(r)}
                        className={`p-1.5 rounded text-xs border ${
                          r.hien_thi ? "hover:bg-amber-50 text-amber-700" : "hover:bg-emerald-50 text-emerald-700"
                        }`}
                        title={r.hien_thi ? "Ẩn đánh giá" : "Hiển thị công khai"}
                      >
                        {r.hien_thi ? <EyeOff className="w-4 h-4 inline" /> : <Eye className="w-4 h-4 inline" />}
                      </button>
                      <button
                        onClick={() => handleDelete(r.id)}
                        className="p-1.5 text-gray-400 hover:text-red-600 rounded hover:bg-gray-100"
                        title="Xóa đánh giá"
                      >
                        <Trash2 className="w-4 h-4 inline" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
