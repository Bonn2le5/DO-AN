import { useRef, useState } from "react";
import { Download, Upload } from "lucide-react";
import CrudPage from "../components/CrudPage";
import { StatusBadge } from "../components/primitives";
import { categoriesStore, foodsStore, importFoodsFile } from "../api/admin.api";
import type { AdminFood } from "../data/mockCatalog";
import { toneGradient, formatCurrency } from "@/lib/utils";
import { useCan } from "../permissions";
import { useToast } from "../components/toast";
import { useAsync } from "@/hooks/useAsync";

const blank: Omit<AdminFood, "id"> = {
  name: "", category: "", price: 0, stock: 0, available: true, spicy: 0, vegetarian: false,
  trackInventory: false, description: "", tone: 1, rating: 0,
};

export default function FoodsPage() {
  const can = useCan();
  const push = useToast((s) => s.push);
  const { data: categories = [] } = useAsync(() => categoriesStore.list(), [categoriesStore]);
  const categoryOptions = categories.map((category) => ({
    value: category.name,
    label: category.active ? category.name : `${category.name} (đang ẩn)`,
  }));
  const input = useRef<HTMLInputElement>(null);
  const [importing, setImporting] = useState(false);
  const downloadTemplate = () => {
    const sampleCategory = categories.find((category) => category.active)?.name ?? "";
    const escape = (value: string) => `"${value.replaceAll('"', '""')}"`;
    const csv = `\uFEFFTên món,Danh mục,Giá,Mô tả,Tồn kho,Độ cay,Món chay,Đang bán,URL hình ảnh\n${escape("Gỏi cuốn")},${escape(sampleCategory)},45000,${escape("Món khai vị tươi ngon")},20,0,Có,Có,\n`;
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "mau-import-mon-an.csv";
    link.click();
    URL.revokeObjectURL(url);
  };
  const selectFile = async (file?: File) => {
    if (!file) return;
    if (!/\.(csv|xlsx|zip)$/i.test(file.name)) {
      push("Vui lòng chọn file .csv, .xlsx hoặc .zip có kèm ảnh.", "err");
      return;
    }
    setImporting(true);
    try {
      const result = await importFoodsFile(file);
      push(result.message || `Đã nhập ${result.created} món ăn.`);
      window.dispatchEvent(new Event("admin:foods-imported"));
    } catch (error) {
      const data = (error as { response?: { data?: { errors?: { row: number; message: string }[]; message?: string; detail?: string } } }).response?.data;
      const detail = data?.errors?.slice(0, 3).map((e) => `Dòng ${e.row}: ${e.message}`).join(" · ") || data?.message || data?.detail;
      push(detail || (error instanceof Error ? error.message : "Không nhập được file."), "err");
    } finally {
      setImporting(false);
      if (input.current) input.current.value = "";
    }
  };
  const importActions = can("foods", "create") ? <>
    <button type="button" className="btn py-2.5! px-4! text-sm!" onClick={downloadTemplate}><Download width={16} height={16} />Tải file mẫu</button>
    <input ref={input} type="file" accept=".csv,.xlsx,.zip" className="hidden" onChange={(e) => void selectFile(e.target.files?.[0])} />
    <button type="button" className="btn py-2.5! px-4! text-sm!" disabled={importing} onClick={() => input.current?.click()}><Upload width={16} height={16} />{importing ? "Đang nhập…" : "Import Excel/CSV/ZIP"}</button>
  </> : null;
  return (
    <CrudPage<AdminFood>
      title="Món ăn" noun="món ăn" module="foods" store={foodsStore} blank={blank}
      subtitle="Nhập CSV/Excel cùng URL ảnh, hoặc ZIP chứa bảng dữ liệu và ảnh món ăn trên máy."
      headerActions={importActions}
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
        { key: "category", label: "Danh mục", type: "select", options: categoryOptions, required: true },
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
