import CrudPage from "../components/CrudPage";
import { StatusBadge } from "../components/primitives";
import { branchesStore } from "../api/admin.api";
import type { AdminBranch } from "../data/mockCatalog";

export default function BranchesPage() {
  return (
    <CrudPage<AdminBranch>
      title="Chi nhánh" noun="chi nhánh" module="branches" store={branchesStore}
      subtitle="Toạ độ dùng để tìm chi nhánh gần khách và chỉ đường trên bản đồ."
      blank={{ name: "", address: "", phone: "", lat: 10.78, lng: 106.69, active: true }}
      searchText={(b) => `${b.name} ${b.address}`} quickToggle={{ key: "active", header: "Hoạt động" }}
      columns={[
        { header: "Chi nhánh", cell: (b) => <div><div className="font-semibold">{b.name}</div><div className="text-xs text-muted">{b.address}</div></div> },
        { header: "Điện thoại", cell: (b) => b.phone },
        { header: "Toạ độ", cell: (b) => <span className="text-muted text-xs">{b.lat.toFixed(4)}, {b.lng.toFixed(4)}</span> },
        { header: "Trạng thái", cell: (b) => <StatusBadge tone={b.active ? "ok" : "neutral"}>{b.active ? "Đang mở" : "Tạm đóng"}</StatusBadge> },
      ]}
      fields={[
        { key: "name", label: "Tên chi nhánh", type: "text", required: true, wide: true },
        { key: "address", label: "Địa chỉ", type: "textarea", required: true },
        { key: "phone", label: "Điện thoại", type: "text" },
        { key: "active", label: "Đang hoạt động", type: "toggle" },
        { key: "lat", label: "Vĩ độ", type: "number", required: true },
        { key: "lng", label: "Kinh độ", type: "number", required: true, hint: "Có thể lấy toạ độ từ Google Maps (nhấp phải vào vị trí)." },
      ]}
    />
  );
}
