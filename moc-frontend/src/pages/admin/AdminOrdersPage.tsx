import { useEffect, useState, useMemo, useCallback } from "react";
import { Search, RefreshCw } from "lucide-react";
import { getMyOrders, type OrderHistoryItem } from "@/api/orders.api";
import { updateAdminOrderStatus } from "@/api/admin.api";
import { useStaffOrderStream, type StaffOrderUpdateEvent } from "@/hooks/useStaffOrderStream";
import type { OrderStatus } from "@/types";

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState<OrderHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchOrders = useCallback(async () => {
    try {
      const data = await getMyOrders();
      setOrders(data);
    } catch (err) {
      console.error("Failed to load orders:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  // Connect to realtime staff order stream
  const { isConnected } = useStaffOrderStream({
    onStatusUpdate: (event: StaffOrderUpdateEvent) => {
      setOrders((prev) =>
        prev.map((o) =>
          String(o.id) === event.orderNumber ||
          String(o.id) === String(event.orderId) ||
          o.orderNumber === event.orderNumber
            ? { ...o, status: event.toStatus as OrderStatus }
            : o
        )
      );
    },
    onOrderCreated: () => {
      fetchOrders();
    },
  });

  const handleStatusChange = async (orderId: number | string, nextStatus: string) => {
    try {
      await updateAdminOrderStatus(orderId, nextStatus);
      fetchOrders();
    } catch (err) {
      alert("Không thể cập nhật trạng thái đơn hàng.");
    }
  };

  const getStatusBadge = (status: string) => {
    const map: Record<string, { label: string; class: string }> = {
      pending: { label: "Chờ tiếp nhận", class: "bg-yellow-100 text-yellow-800" },
      cho_tiep_nhan: { label: "Chờ tiếp nhận", class: "bg-yellow-100 text-yellow-800" },
      confirmed: { label: "Đã xác nhận", class: "bg-blue-100 text-blue-800" },
      da_xac_nhan: { label: "Đã xác nhận", class: "bg-blue-100 text-blue-800" },
      preparing: { label: "Đang chế biến", class: "bg-orange-100 text-orange-800" },
      dang_che_bien: { label: "Đang chế biến", class: "bg-orange-100 text-orange-800" },
      ready: { label: "Sẵn sàng", class: "bg-teal-100 text-teal-800" },
      san_sang: { label: "Sẵn sàng", class: "bg-teal-100 text-teal-800" },
      completed: { label: "Hoàn tất", class: "bg-green-100 text-green-800" },
      hoan_tat: { label: "Hoàn tất", class: "bg-green-100 text-green-800" },
      cancelled: { label: "Đã hủy", class: "bg-red-100 text-red-800" },
      da_huy: { label: "Đã hủy", class: "bg-red-100 text-red-800" },
    };
    const s = map[status] || { label: status, class: "bg-gray-100 text-gray-800" };
    return <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${s.class}`}>{s.label}</span>;
  };

  const filteredOrders = useMemo(() => {
    return orders.filter((o) => {
      const matchStatus =
        statusFilter === "all" ||
        o.status === statusFilter ||
        (statusFilter === "cho_tiep_nhan" && o.status === "pending") ||
        (statusFilter === "da_xac_nhan" && o.status === "confirmed") ||
        (statusFilter === "dang_che_bien" && o.status === "preparing") ||
        (statusFilter === "san_sang" && o.status === "ready") ||
        (statusFilter === "hoan_tat" && o.status === "completed") ||
        (statusFilter === "da_huy" && o.status === "cancelled");

      const matchSearch =
        !searchQuery ||
        String(o.orderNumber || o.id).toLowerCase().includes(searchQuery.toLowerCase());

      return matchStatus && matchSearch;
    });
  }, [orders, statusFilter, searchQuery]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Quản lý Đơn hàng</h1>
          <div className="flex items-center gap-2 mt-1">
            <span className={`w-2 h-2 rounded-full ${isConnected ? "bg-emerald-500 animate-pulse" : "bg-amber-400"}`} />
            <span className="text-xs text-gray-500">
              {isConnected ? "Kênh giám sát đơn trực tiếp (Real-time)" : "Đang kết nối lại..."}
            </span>
          </div>
        </div>
        <button
          onClick={fetchOrders}
          className="p-2 border rounded-lg hover:bg-gray-100 text-gray-600 transition-colors"
          title="Làm mới"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
        <div className="p-4 border-b flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
            <input
              type="text"
              placeholder="Tìm theo mã đơn hàng..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border rounded-lg text-sm bg-white"
          >
            <option value="all">Tất cả trạng thái</option>
            <option value="cho_tiep_nhan">Chờ tiếp nhận</option>
            <option value="da_xac_nhan">Đã xác nhận</option>
            <option value="dang_che_bien">Đang chế biến</option>
            <option value="san_sang">Sẵn sàng</option>
            <option value="hoan_tat">Hoàn tất</option>
            <option value="da_huy">Đã hủy</option>
          </select>
        </div>

        {loading ? (
          <div className="p-12 text-center text-gray-500">Đang tải dữ liệu đơn hàng...</div>
        ) : filteredOrders.length === 0 ? (
          <div className="p-12 text-center text-gray-400">Không tìm thấy đơn hàng nào.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 border-b text-gray-600 font-medium">
                <tr>
                  <th className="p-3.5">Mã đơn</th>
                  <th className="p-3.5">Thời gian</th>
                  <th className="p-3.5">Món ăn</th>
                  <th className="p-3.5">Tổng tiền</th>
                  <th className="p-3.5">Trạng thái</th>
                  <th className="p-3.5 text-right">Chuyển trạng thái FSM</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredOrders.map((o) => (
                  <tr key={o.id} className="hover:bg-gray-50/70 transition-colors">
                    <td className="p-3.5 font-semibold text-gray-900">{o.id}</td>
                    <td className="p-3.5 text-xs text-gray-600">
                      {new Date(o.createdAt).toLocaleString("vi-VN")}
                    </td>
                    <td className="p-3.5 text-gray-700">{o.items} món</td>
                    <td className="p-3.5 font-bold text-gray-900">
                      {Number(o.total).toLocaleString()}đ
                    </td>
                    <td className="p-3.5">{getStatusBadge(o.status)}</td>
                    <td className="p-3.5 text-right space-x-1.5">
                      {(o.status === "pending" || o.status === "cho_tiep_nhan") && (
                        <button
                          onClick={() => handleStatusChange(o.id, "da_xac_nhan")}
                          className="px-2.5 py-1 text-xs bg-blue-50 text-blue-700 border border-blue-200 rounded font-medium hover:bg-blue-100"
                        >
                          Xác nhận
                        </button>
                      )}
                      {(o.status === "confirmed" || o.status === "da_xac_nhan") && (
                        <button
                          onClick={() => handleStatusChange(o.id, "dang_che_bien")}
                          className="px-2.5 py-1 text-xs bg-orange-50 text-orange-700 border border-orange-200 rounded font-medium hover:bg-orange-100"
                        >
                          Nấu món
                        </button>
                      )}
                      {(o.status === "preparing" || o.status === "dang_che_bien") && (
                        <button
                          onClick={() => handleStatusChange(o.id, "san_sang")}
                          className="px-2.5 py-1 text-xs bg-teal-50 text-teal-700 border border-teal-200 rounded font-medium hover:bg-teal-100"
                        >
                          Sẵn sàng
                        </button>
                      )}
                      {(o.status === "ready" || o.status === "san_sang") && (
                        <button
                          onClick={() => handleStatusChange(o.id, "hoan_tat")}
                          className="px-2.5 py-1 text-xs bg-green-50 text-green-700 border border-green-200 rounded font-medium hover:bg-green-100"
                        >
                          Hoàn tất
                        </button>
                      )}
                      {o.status !== "completed" && o.status !== "hoan_tat" && o.status !== "cancelled" && o.status !== "da_huy" && (
                        <button
                          onClick={() => handleStatusChange(o.id, "da_huy")}
                          className="px-2 py-1 text-xs text-red-600 hover:bg-red-50 rounded"
                        >
                          Hủy
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
    </div>
  );
}