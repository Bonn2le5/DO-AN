import CrudPage from "../components/CrudPage";
import { StatusBadge } from "../components/primitives";
import { promotionsStore } from "../api/admin.api";
import { fmtDateTime } from "../lib";
import { formatCurrency } from "@/lib/utils";
import type { AdminPromotion } from "../data/mockCatalog";

const blank: Omit<AdminPromotion, "id"> = {
  code: "", name: "", discountType: "percent", discountValue: 10, minOrder: 0, maxDiscount: 0,
  startAt: "", endAt: "", usageLimit: 0, usedCount: 0, active: true,
};

export default function PromotionsPage() {
  return (
    <CrudPage<AdminPromotion>
      title="Khuyến mãi" noun="khuyến mãi" module="promotions" store={promotionsStore} blank={blank}
      subtitle="Mã giảm giá theo % hoặc số tiền cố định. Giới hạn lượt dùng bằng 0 nghĩa là không giới hạn."
      searchText={(p) => `${p.code} ${p.name}`} quickToggle={{ key: "active", header: "Đang chạy" }}
      columns={[
        { header: "Mã", cell: (p) => <b className="tracking-wide">{p.code}</b> },
        { header: "Chương trình", cell: (p) => p.name },
        { header: "Mức giảm", cell: (p) => (p.discountType === "percent" ? `${p.discountValue}%` : formatCurrency(p.discountValue)) },
        { header: "Đã dùng", cell: (p) => (p.usageLimit ? `${p.usedCount}/${p.usageLimit}` : p.usedCount) },
        { header: "Hiệu lực", cell: (p) => {
          const now = Date.now();
          const live = new Date(p.startAt).getTime() <= now && now <= new Date(p.endAt).getTime();
          return <div><StatusBadge tone={live ? "ok" : "neutral"}>{live ? "Trong thời hạn" : "Ngoài thời hạn"}</StatusBadge><div className="text-xs text-muted mt-1">đến {fmtDateTime(p.endAt)}</div></div>;
        } },
      ]}
      fields={[
        { key: "code", label: "Mã khuyến mãi", type: "text", required: true },
        { key: "name", label: "Tên chương trình", type: "text", required: true },
        { key: "discountType", label: "Hình thức giảm", type: "select", required: true, options: [{ value: "percent", label: "Theo phần trăm" }, { value: "fixed", label: "Số tiền cố định" }] },
        { key: "discountValue", label: "Giá trị giảm", type: "number", required: true },
        { key: "minOrder", label: "Đơn tối thiểu (đ)", type: "number" },
        { key: "maxDiscount", label: "Giảm tối đa (đ)", type: "number", hint: "Chỉ áp dụng cho giảm theo %. Để 0 nếu không giới hạn." },
        { key: "startAt", label: "Bắt đầu", type: "datetime", required: true },
        { key: "endAt", label: "Kết thúc", type: "datetime", required: true },
        { key: "usageLimit", label: "Giới hạn lượt dùng", type: "number" },
        { key: "active", label: "Đang chạy", type: "toggle" },
      ]}
    />
  );
}
