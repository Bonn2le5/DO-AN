import { useState } from "react";
import CrudPage from "../components/CrudPage";
import { PageHeader, StatusBadge, Tabs } from "../components/primitives";
import { categoriesStore, tagsStore } from "../api/admin.api";
import type { AdminCategory, AdminTag } from "../data/mockCatalog";

export default function CategoriesPage() {
  const [tab, setTab] = useState<"cat" | "tag">("cat");
  return (
    <div>
      <PageHeader title="Danh mục & tag" subtitle="Danh mục dùng để lọc thực đơn; tag giúp gợi ý món và tìm kiếm." />
      <div className="mb-5"><Tabs value={tab} onChange={setTab} items={[{ key: "cat", label: "Danh mục" }, { key: "tag", label: "Tag" }]} /></div>
      {tab === "cat" ? (
        <CrudPage<AdminCategory>
          hideHeader title="" noun="danh mục" module="categories" store={categoriesStore}
          blank={{ name: "", description: "", active: true }}
          searchText={(c) => c.name} quickToggle={{ key: "active", header: "Hiển thị" }}
          columns={[
            { header: "Tên", cell: (c) => <b>{c.name}</b> },
            { header: "Mô tả", cell: (c) => <span className="text-muted">{c.description}</span> },
            { header: "Trạng thái", cell: (c) => <StatusBadge tone={c.active ? "ok" : "neutral"}>{c.active ? "Đang hiện" : "Đang ẩn"}</StatusBadge> },
          ]}
          fields={[
            { key: "name", label: "Tên danh mục", type: "text", required: true },
            { key: "description", label: "Mô tả", type: "textarea" },
            { key: "active", label: "Hiển thị trên website", type: "toggle" },
          ]}
        />
      ) : (
        <CrudPage<AdminTag>
          hideHeader title="" noun="tag" module="categories" store={tagsStore} blank={{ name: "" }}
          searchText={(t) => t.name}
          columns={[{ header: "Tên tag", cell: (t) => <b>{t.name}</b> }]}
          fields={[{ key: "name", label: "Tên tag", type: "text", required: true }]}
        />
      )}
    </div>
  );
}
