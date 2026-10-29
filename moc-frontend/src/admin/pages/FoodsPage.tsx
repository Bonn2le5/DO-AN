import CrudPage from "../components/CrudPage";
import { StatusBadge } from "../components/primitives";
import { foodsStore } from "../api/admin.api";
import { CATEGORY_OPTIONS, type AdminFood } from "../data/mockCatalog";
import { toneGradient, formatCurrency } from "@/lib/utils";

const blank: Omit<AdminFood, "id"> = {
  name: "", category: "Món chính", price: 0, stock: 0, available: true, spicy: 0, vegetarian: false,
  trackInventory: false, description: "", tone: 1, rating: 0,
};

export default function FoodsPage() {
  return (
    <CrudPage<AdminFood>
      title="Món ăn" noun="món ăn" module="foods" store={foodsStore} blank={blank}
      subtitle="Quản lý thực đơn, giá bán và tình trạng còn hàng."
      searchText={(f) => `${f.name} ${f.category}`}
      quickToggle={{ key: "available", header: "Còn hàng" }}
      columns={[
        { header: "Món", cell: (f) => (
          <div className="flex items-center gap-3 min-w-52">
            {f.image
              ? <img src={f.image} alt="" className="w-11 h-11 rounded-lg object-cover" />
              : <span className="w-11 h-11 rounded-lg shrink-0" style={{ background: toneGradient(f.tone) }} />}
            <div><div className="font-semibold">{f.name}</div><div className="text-xs text-muted line-clamp-1">{f.description}</div></div>
          </div>
        ) },
        { header: "Danh mục", cell: (f) => f.category },
        { header: "Giá", cell: (f) => <b>{formatCurrency(f.price)}</b> },
        { header: "Tồn kho", cell: (f) => (f.trackInventory ? <StatusBadge>Theo nguyên liệu</StatusBadge> : f.stock) },
        { header: "Đánh giá", cell: (f) => (f.rating ? f.rating.toFixed(1) : "—") },
      ]}
      fields={[
        { key: "image", label: "Ảnh món", type: "image" },
        { key: "name", label: "Tên món", type: "text", required: true, wide: true },
        { key: "category", label: "Danh mục", type: "select", options: CATEGORY_OPTIONS, required: true },
        { key: "price", label: "Giá bán (đ)", type: "number", required: true },
        { key: "spicy", label: "Độ cay", type: "select", options: [0, 1, 2, 3].map((n) => ({ value: String(n), label: n === 0 ? "Không cay" : `Cay mức ${n}` })) },
        { key: "stock", label: "Số phần còn", type: "number", hint: "Bỏ qua nếu tồn kho tính theo nguyên liệu." },
        { key: "description", label: "Mô tả", type: "textarea" },
        { key: "vegetarian", label: "Món chay", type: "toggle" },
        { key: "available", label: "Đang bán", type: "toggle" },
        { key: "trackInventory", label: "Trừ kho theo nguyên liệu", type: "toggle" },
      ]}
    />
  );
}
