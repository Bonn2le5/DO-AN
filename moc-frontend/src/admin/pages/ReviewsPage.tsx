import { reviewsStore } from "../api/admin.api";
import CrudPage from "../components/CrudPage";
import { StatusBadge } from "../components/primitives";
import RatingStars from "@/components/ui/RatingStars";
import { fmtDateTime } from "../lib";
import type { AdminReview } from "../data/mockCatalog";

export default function ReviewsPage() {
  return (
    <CrudPage<AdminReview>
      title="Đánh giá" noun="đánh giá" module="reviews" store={reviewsStore}
      hideAdd hideDelete
      subtitle="Ẩn đánh giá không phù hợp thay vì xoá. Điểm trung bình của món sẽ tính lại từ các đánh giá đang hiện."
      blank={{ food: "", customer: "", rating: 5, comment: "", visible: true, createdAt: new Date().toISOString() }}
      searchText={(r) => `${r.food} ${r.customer} ${r.comment}`} quickToggle={{ key: "visible", header: "Hiển thị" }}
      columns={[
        { header: "Món", cell: (r) => <b>{r.food}</b> },
        { header: "Khách", cell: (r) => r.customer },
        { header: "Điểm", cell: (r) => <RatingStars rating={r.rating} size={13} /> },
        { header: "Nội dung", cell: (r) => <div className="max-w-sm line-clamp-2 text-muted">{r.comment}</div> },
        { header: "Ngày", cell: (r) => fmtDateTime(r.createdAt) },
        { header: "Trạng thái", cell: (r) => <StatusBadge tone={r.visible ? "ok" : "neutral"}>{r.visible ? "Đang hiện" : "Đã ẩn"}</StatusBadge> },
      ]}
      fields={[
        { key: "comment", label: "Nội dung đánh giá", type: "textarea" },
        { key: "visible", label: "Hiển thị công khai", type: "toggle" },
      ]}
    />
  );
}
