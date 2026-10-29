import { useEffect, useState, useMemo } from "react";
import {
  Users,
  Search,
  Plus,
  RefreshCw,
  Eye,
  AlertTriangle,
} from "lucide-react";
import {
  getAdminTables,
  getAdminReservations,
  updateReservationStatus,
  cancelReservationAdmin,
  createAdminTable,
  updateAdminTable,
  deleteAdminTable,
  type AdminTableItem,
  type AdminReservationItem,
} from "@/api/admin.api";

export default function AdminReservationsPage() {
  const [activeTab, setActiveTab] = useState<"reservations" | "tables">("reservations");
  const [tables, setTables] = useState<AdminTableItem[]>([]);
  const [reservations, setReservations] = useState<AdminReservationItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [dateFilter, setDateFilter] = useState("");

  // Modals
  const [selectedRes, setSelectedRes] = useState<AdminReservationItem | null>(null);
  const [cancelModalRes, setCancelModalRes] = useState<AdminReservationItem | null>(null);
  const [cancelReason, setCancelReason] = useState("");
  const [isNoShow, setIsNoShow] = useState(false);
  const [tableModalOpen, setTableModalOpen] = useState(false);
  const [editingTable, setEditingTable] = useState<Partial<AdminTableItem> | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [tList, rList] = await Promise.all([getAdminTables(), getAdminReservations()]);
      setTables(tList);
      setReservations(rList);
    } catch (err) {
      console.error("Failed to load tables/reservations:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleStatusChange = async (resId: number, newStatus: string) => {
    try {
      await updateReservationStatus(resId, newStatus);
      fetchData();
    } catch (err) {
      alert("Không thể cập nhật trạng thái đặt bàn.");
    }
  };

  const handleConfirmCancel = async () => {
    if (!cancelModalRes) return;
    try {
      const res = await cancelReservationAdmin(cancelModalRes.id, cancelReason || "Nhân viên hủy", isNoShow);
      alert(
        `Đã hủy đặt bàn thành công! Hoàn cọc: ${res.phan_tram_hoan_tien}% (${res.so_tien_hoan.toLocaleString()}đ)`
      );
      setCancelModalRes(null);
      setCancelReason("");
      setIsNoShow(false);
      fetchData();
    } catch (err) {
      alert("Lỗi khi xử lý hủy đặt bàn.");
    }
  };

  const handleSaveTable = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTable) return;
    try {
      if (editingTable.id) {
        await updateAdminTable(editingTable.id, editingTable);
      } else {
        await createAdminTable({
          chi_nhanh: 1,
          so_ban: editingTable.so_ban || "B01",
          khu_vuc: editingTable.khu_vuc || "Tầng 1",
          suc_chua: Number(editingTable.suc_chua || 4),
          trang_thai: editingTable.trang_thai || "trong",
        });
      }
      setTableModalOpen(false);
      setEditingTable(null);
      fetchData();
    } catch (err) {
      alert("Lỗi khi lưu thông tin bàn.");
    }
  };

  const handleDeleteTable = async (id: number) => {
    if (!confirm("Bạn có chắc chắn muốn xóa bàn này không?")) return;
    try {
      await deleteAdminTable(id);
      fetchData();
    } catch (err) {
      alert("Không thể xóa bàn đang có dữ liệu liên quan.");
    }
  };

  const filteredReservations = useMemo(() => {
    return reservations.filter((r) => {
      const matchStatus = statusFilter === "all" || r.trang_thai === statusFilter;
      const matchDate = !dateFilter || r.ngay_dat === dateFilter;
      const matchSearch =
        !searchQuery ||
        r.ma_dat_ban.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.ten_khach.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.sdt_khach.includes(searchQuery);
      return matchStatus && matchDate && matchSearch;
    });
  }, [reservations, statusFilter, dateFilter, searchQuery]);

  const tablesByZone = useMemo(() => {
    const map: Record<string, AdminTableItem[]> = {};
    tables.forEach((t) => {
      const zone = t.khu_vuc || "Chung";
      if (!map[zone]) map[zone] = [];
      map[zone].push(t);
    });
    return map;
  }, [tables]);

  const getResBadge = (status: string) => {
    const map: Record<string, { label: string; cls: string }> = {
      cho_xac_nhan: { label: "Chờ nhà hàng xác nhận", cls: "bg-amber-100 text-amber-800" },
      cho_thanh_toan: { label: "Chờ thanh toán", cls: "bg-amber-100 text-amber-800" },
      da_xac_nhan: { label: "Đã xác nhận", cls: "bg-blue-100 text-blue-800" },
      khach_da_den: { label: "Khách đã đến", cls: "bg-purple-100 text-purple-800" },
      hoan_tat: { label: "Hoàn tất", cls: "bg-green-100 text-green-800" },
      da_huy: { label: "Đã hủy", cls: "bg-red-100 text-red-800" },
      khach_khong_den: { label: "Khách không đến", cls: "bg-gray-100 text-gray-800" },
    };
    const s = map[status] || { label: status, cls: "bg-gray-100 text-gray-700" };
    return <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${s.cls}`}>{s.label}</span>;
  };

  const getTableColor = (status: string) => {
    switch (status) {
      case "trong":
        return "bg-emerald-50 border-emerald-300 text-emerald-800 hover:bg-emerald-100";
      case "dang_giu":
        return "bg-amber-50 border-amber-300 text-amber-800 hover:bg-amber-100";
      case "da_dat":
        return "bg-blue-50 border-blue-300 text-blue-800 hover:bg-blue-100";
      case "dang_phuc_vu":
        return "bg-indigo-50 border-indigo-300 text-indigo-800 hover:bg-indigo-100";
      case "bao_tri":
        return "bg-gray-100 border-gray-300 text-gray-600 hover:bg-gray-200";
      default:
        return "bg-gray-50 border-gray-200 text-gray-700";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Quản lý Bàn ăn & Đặt bàn</h1>
          <p className="text-sm text-gray-500">Giám sát sơ đồ bàn trực tiếp và xử lý danh sách phiếu đặt bàn.</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchData}
            className="p-2 border rounded-lg hover:bg-gray-100 text-gray-600 transition-colors"
            title="Làm mới"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <div className="flex bg-gray-200 p-1 rounded-lg text-sm">
            <button
              onClick={() => setActiveTab("reservations")}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === "reservations" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Danh sách đặt bàn ({reservations.length})
            </button>
            <button
              onClick={() => setActiveTab("tables")}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === "tables" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Sơ đồ bàn ăn ({tables.length})
            </button>
          </div>
        </div>
      </div>

      {/* TAB 1: RESERVATIONS */}
      {activeTab === "reservations" && (
        <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
          {/* Filters Bar */}
          <div className="p-4 border-b flex flex-col md:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
              <input
                type="text"
                placeholder="Tìm mã đặt bàn, tên khách, số điện thoại..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <div className="flex gap-2">
              <input
                type="date"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
                className="px-3 py-2 border rounded-lg text-sm bg-white"
              />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border rounded-lg text-sm bg-white"
              >
                <option value="all">Tất cả trạng thái</option>
                <option value="cho_xac_nhan">Chờ nhà hàng xác nhận</option>
                <option value="cho_thanh_toan">Chờ thanh toán</option>
                <option value="da_xac_nhan">Đã xác nhận</option>
                <option value="khach_da_den">Khách đã đến</option>
                <option value="hoan_tat">Hoàn tất</option>
                <option value="da_huy">Đã hủy</option>
                <option value="khach_khong_den">Khách không đến</option>
              </select>
            </div>
          </div>

          {/* Table */}
          {loading ? (
            <div className="p-12 text-center text-gray-500">Đang tải dữ liệu...</div>
          ) : filteredReservations.length === 0 ? (
            <div className="p-12 text-center text-gray-400">Không tìm thấy phiếu đặt bàn nào phù hợp.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-50 border-b text-gray-600 font-medium">
                  <tr>
                    <th className="p-3.5">Mã phiếu</th>
                    <th className="p-3.5">Khách hàng</th>
                    <th className="p-3.5">Bàn & Khách</th>
                    <th className="p-3.5">Thời gian đến</th>
                    <th className="p-3.5">Tiền cọc</th>
                    <th className="p-3.5">Trạng thái</th>
                    <th className="p-3.5 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredReservations.map((r) => (
                    <tr key={r.id} className="hover:bg-gray-50/70 transition-colors">
                      <td className="p-3.5 font-semibold text-gray-900">{r.ma_dat_ban}</td>
                      <td className="p-3.5">
                        <div className="font-medium text-gray-900">{r.ten_khach}</div>
                        <div className="text-xs text-gray-500">{r.sdt_khach}</div>
                      </td>
                      <td className="p-3.5">
                        <span className="font-medium">{r.so_ban ? `Bàn ${r.so_ban}` : "Chưa gán"}</span>
                        <span className="text-xs text-gray-500 block">({r.so_luong_khach} người)</span>
                      </td>
                      <td className="p-3.5">
                        <div className="font-medium">{r.gio_bat_dau.slice(0, 5)}</div>
                        <div className="text-xs text-gray-500">{r.ngay_dat}</div>
                      </td>
                      <td className="p-3.5">
                        <div className="font-medium">{Number(r.so_tien_coc).toLocaleString()}đ</div>
                        <div className="text-[11px] text-gray-400">{r.trang_thai_coc}</div>
                      </td>
                      <td className="p-3.5">{getResBadge(r.trang_thai)}</td>
                      <td className="p-3.5 text-right space-x-1">
                        <button
                          onClick={() => setSelectedRes(r)}
                          className="px-2 py-1 text-xs border rounded text-gray-600 hover:bg-gray-100"
                          title="Xem chi tiết"
                        >
                          <Eye className="w-3.5 h-3.5 inline" />
                        </button>
                        {r.trang_thai === "da_xac_nhan" && (
                          <button
                            onClick={() => handleStatusChange(r.id, "khach_da_den")}
                            className="px-2 py-1 text-xs bg-purple-50 text-purple-700 border border-purple-200 rounded hover:bg-purple-100 font-medium"
                          >
                            Đã đến
                          </button>
                        )}
                        {r.trang_thai === "khach_da_den" && (
                          <button
                            onClick={() => handleStatusChange(r.id, "hoan_tat")}
                            className="px-2 py-1 text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 rounded hover:bg-emerald-100 font-medium"
                          >
                            Hoàn tất
                          </button>
                        )}
                        {["cho_xac_nhan", "cho_thanh_toan", "da_xac_nhan"].includes(r.trang_thai) && (
                          <button
                            onClick={() => setCancelModalRes(r)}
                            className="px-2 py-1 text-xs bg-red-50 text-red-600 border border-red-200 rounded hover:bg-red-100 font-medium"
                          >
                            Hủy / Hoàn cọc
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: TABLE FLOOR MAP */}
      {activeTab === "tables" && (
        <div className="space-y-6">
          <div className="flex justify-between items-center bg-white p-4 border rounded-xl shadow-sm">
            <div className="flex flex-wrap gap-4 text-xs font-medium">
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-emerald-500" /> Trống</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-amber-500" /> Đang giữ 10p</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-blue-500" /> Đã đặt</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-indigo-500" /> Đang phục vụ</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-gray-400" /> Bảo trì</span>
            </div>
            <button
              onClick={() => {
                setEditingTable({ chi_nhanh: 1, so_ban: "", khu_vuc: "Tầng 1", suc_chua: 4, trang_thai: "trong" });
                setTableModalOpen(true);
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-white text-sm rounded-lg hover:bg-primary/90"
            >
              <Plus className="w-4 h-4" /> Thêm bàn
            </button>
          </div>

          {/* Zones */}
          {Object.entries(tablesByZone).map(([zone, zoneTables]) => (
            <div key={zone} className="bg-white border rounded-xl p-5 shadow-sm space-y-4">
              <h3 className="font-bold text-gray-800 text-lg flex items-center gap-2 border-b pb-2">
                <span>📍 {zone}</span>
                <span className="text-xs font-normal text-gray-500">({zoneTables.length} bàn)</span>
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {zoneTables.map((t) => (
                  <div
                    key={t.id}
                    className={`border-2 rounded-xl p-4 flex flex-col justify-between transition-all shadow-sm ${getTableColor(
                      t.trang_thai
                    )}`}
                  >
                    <div className="flex justify-between items-start">
                      <span className="text-lg font-bold">Bàn {t.so_ban}</span>
                      <span className="text-xs font-medium flex items-center gap-0.5">
                        <Users className="w-3.5 h-3.5" /> {t.suc_chua}
                      </span>
                    </div>

                    <div className="mt-4 pt-2 border-t border-black/10 flex justify-between items-center text-xs">
                      <select
                        value={t.trang_thai}
                        onChange={async (e) => {
                          const newStatus = e.target.value as AdminTableItem["trang_thai"];
                          await updateAdminTable(t.id, { trang_thai: newStatus });
                          fetchData();
                        }}
                        className="bg-transparent font-medium border-0 focus:ring-0 p-0 text-xs cursor-pointer"
                      >
                        <option value="trong">Trống</option>
                        <option value="dang_giu">Đang giữ</option>
                        <option value="da_dat">Đã đặt</option>
                        <option value="dang_phuc_vu">Đang dùng</option>
                        <option value="bao_tri">Bảo trì</option>
                      </select>
                      <button
                        onClick={() => handleDeleteTable(t.id)}
                        className="text-red-500 hover:text-red-700 ml-2"
                        title="Xóa bàn"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* DETAIL MODAL */}
      {selectedRes && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex justify-between items-center border-b pb-3">
              <h3 className="font-bold text-lg">Chi tiết phiếu đặt: {selectedRes.ma_dat_ban}</h3>
              <button onClick={() => setSelectedRes(null)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div className="space-y-2 text-sm text-gray-700">
              <p><strong>Khách hàng:</strong> {selectedRes.ten_khach} - {selectedRes.sdt_khach}</p>
              <p><strong>Bàn & Số khách:</strong> Bàn {selectedRes.so_ban || "Chưa gán"} ({selectedRes.so_luong_khach} khách)</p>
              <p><strong>Thời gian:</strong> {selectedRes.gio_bat_dau} ngày {selectedRes.ngay_dat}</p>
              <p><strong>Hình thức:</strong> {selectedRes.hinh_thuc}</p>
              <p><strong>Tiền đặt cọc:</strong> {Number(selectedRes.so_tien_coc).toLocaleString()}đ ({selectedRes.trang_thai_coc})</p>
              {selectedRes.ghi_chu && <p><strong>Ghi chú:</strong> {selectedRes.ghi_chu}</p>}

              {selectedRes.danh_sach_mon && selectedRes.danh_sach_mon.length > 0 && (
                <div className="mt-3 pt-3 border-t">
                  <h4 className="font-bold mb-2">Món ăn đặt trước:</h4>
                  <ul className="space-y-1">
                    {selectedRes.danh_sach_mon.map((m) => (
                      <li key={m.id} className="flex justify-between text-xs">
                        <span>{m.mon_an?.ten} x{m.so_luong}</span>
                        <span>{Number(m.don_gia_luc_dat * m.so_luong).toLocaleString()}đ</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <div className="pt-3 border-t flex justify-end">
              <button
                onClick={() => setSelectedRes(null)}
                className="px-4 py-2 bg-gray-100 rounded-lg text-sm text-gray-700 hover:bg-gray-200"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CANCEL & REFUND MODAL */}
      {cancelModalRes && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center gap-2 text-red-600 font-bold text-lg border-b pb-3">
              <AlertTriangle className="w-5 h-5" /> Hủy đặt bàn & Tính hoàn cọc
            </div>
            <p className="text-sm text-gray-600">
              Bạn đang thực hiện hủy phiếu <strong>{cancelModalRes.ma_dat_ban}</strong> của khách <strong>{cancelModalRes.ten_khach}</strong>. Hệ thống sẽ tự động đối chiếu thời gian và sinh phiếu hoàn tiền theo quy định.
            </p>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-gray-700 block mb-1">Lý do hủy:</label>
                <input
                  type="text"
                  placeholder="Khách báo bận, sự cố..."
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isNoShow}
                  onChange={(e) => setIsNoShow(e.target.checked)}
                  className="rounded text-primary focus:ring-primary"
                />
                Khách không đến (No-show - Phạt 100% cọc)
              </label>
            </div>
            <div className="pt-3 border-t flex justify-end gap-2">
              <button
                onClick={() => setCancelModalRes(null)}
                className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-100"
              >
                Hủy bỏ
              </button>
              <button
                onClick={handleConfirmCancel}
                className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 font-medium"
              >
                Xác nhận Hủy
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TABLE MODAL */}
      {tableModalOpen && editingTable && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <form onSubmit={handleSaveTable} className="bg-white rounded-xl shadow-xl max-w-sm w-full p-6 space-y-4">
            <h3 className="font-bold text-lg border-b pb-3">
              {editingTable.id ? "Chỉnh sửa bàn" : "Thêm bàn ăn mới"}
            </h3>
            <div className="space-y-3 text-sm">
              <div>
                <label className="block text-xs font-semibold mb-1">Số bàn / Tên bàn:</label>
                <input
                  type="text"
                  required
                  placeholder="B01, VIP1..."
                  value={editingTable.so_ban || ""}
                  onChange={(e) => setEditingTable({ ...editingTable, so_ban: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Khu vực:</label>
                <input
                  type="text"
                  required
                  placeholder="Tầng 1, Tầng 2, Ngoài trời..."
                  value={editingTable.khu_vuc || ""}
                  onChange={(e) => setEditingTable({ ...editingTable, khu_vuc: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Sức chứa (số ghế):</label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  required
                  value={editingTable.suc_chua || 4}
                  onChange={(e) => setEditingTable({ ...editingTable, suc_chua: Number(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>
            <div className="pt-3 border-t flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setTableModalOpen(false)}
                className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-100"
              >
                Hủy
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90"
              >
                Lưu
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
