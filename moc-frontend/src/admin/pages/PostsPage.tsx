import CrudPage from "../components/CrudPage";
import { StatusBadge } from "../components/primitives";
import { postsStore } from "../api/admin.api";
import { fmtDateTime } from "../lib";
import type { AdminPost } from "../data/mockCatalog";

const STATUS = { draft: { label: "Bản nháp", tone: "neutral" }, published: { label: "Đã xuất bản", tone: "ok" }, archived: { label: "Lưu trữ", tone: "warn" } } as const;

export default function PostsPage() {
  return (
    <CrudPage<AdminPost>
      title="Bài viết" noun="bài viết" module="posts" store={postsStore}
      subtitle="Viết và xuất bản bài cho trang “Câu chuyện từ căn bếp”."
      blank={{ title: "", category: "Ẩm thực", status: "draft", content: "", createdAt: new Date().toISOString() }}
      searchText={(p) => `${p.title} ${p.category}`}
      columns={[
        { header: "Tiêu đề", cell: (p) => <div className="max-w-md font-semibold line-clamp-2">{p.title}</div> },
        { header: "Chuyên mục", cell: (p) => p.category },
        { header: "Trạng thái", cell: (p) => <StatusBadge tone={STATUS[p.status].tone}>{STATUS[p.status].label}</StatusBadge> },
        { header: "Ngày tạo", cell: (p) => fmtDateTime(p.createdAt) },
      ]}
      fields={[
        { key: "image", label: "Ảnh đại diện", type: "image" },
        { key: "title", label: "Tiêu đề", type: "text", required: true, wide: true },
        { key: "category", label: "Chuyên mục", type: "select", options: ["Ẩm thực", "Sự kiện", "Công thức"].map((v) => ({ value: v, label: v })) },
        { key: "status", label: "Trạng thái", type: "select", options: [{ value: "draft", label: "Bản nháp" }, { value: "published", label: "Xuất bản" }, { value: "archived", label: "Lưu trữ" }] },
        { key: "content", label: "Nội dung", type: "textarea", required: true },
      ]}
    />
  );
}
