import { useEffect, useState, useMemo } from "react";
import {
  Package,
  Plus,
  Search,
  Edit,
  Trash2,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import {
  getAdminFoods,
  getAdminCategories,
  createAdminFood,
  updateAdminFood,
  deleteAdminFood,
  getAdminIngredients,
  getAdminInventoryTransactions,
  createInventoryTransaction,
  type AdminFoodItem,
  type AdminCategoryItem,
  type AdminIngredientItem,
  type AdminInventoryTransactionItem,
} from "@/api/admin.api";

export default function AdminMenuPage() {
  const [activeTab, setActiveTab] = useState<"foods" | "ingredients" | "transactions">("foods");
  const [foods, setFoods] = useState<AdminFoodItem[]>([]);
  const [categories, setCategories] = useState<AdminCategoryItem[]>([]);
  const [ingredients, setIngredients] = useState<AdminIngredientItem[]>([]);
  const [transactions, setTransactions] = useState<AdminInventoryTransactionItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [catFilter, setCatFilter] = useState("all");

  // Food Modal
  const [foodModalOpen, setFoodModalOpen] = useState(false);
  const [editingFood, setEditingFood] = useState<Partial<AdminFoodItem> | null>(null);

  // Inventory Transaction Modal
  const [txModalOpen, setTxModalOpen] = useState(false);
  const [txData, setTxData] = useState<{
    nguyen_lieu: number;
    loai_giao_dich: "nhap" | "xuat" | "dieu_chinh";
    so_luong: number;
    ghi_chu: string;
  }>({
    nguyen_lieu: 0,
    loai_giao_dich: "nhap",
    so_luong: 1,
    ghi_chu: "",
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [fList, cList, iList, tList] = await Promise.all([
        getAdminFoods(),
        getAdminCategories(),
        getAdminIngredients(),
        getAdminInventoryTransactions(),
      ]);
      setFoods(fList);
      setCategories(cList);
      setIngredients(iList);
      setTransactions(tList);
      if (iList.length > 0 && !txData.nguyen_lieu) {
        setTxData((prev) => ({ ...prev, nguyen_lieu: iList[0].id }));
      }
    } catch (err) {
      console.error("Failed to load menu data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleToggleFoodStatus = async (food: AdminFoodItem, field: "con_hang" | "hien_thi") => {
    try {
      await updateAdminFood(food.duong_dan, { [field]: !food[field] });
      fetchData();
    } catch (err) {
      alert("Không thể cập nhật trạng thái món ăn.");
    }
  };

  const handleSaveFood = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingFood) return;
    try {
      if (editingFood.duong_dan) {
        await updateAdminFood(editingFood.duong_dan, editingFood);
      } else {
        await createAdminFood({
          ...editingFood,
          danh_muc: editingFood.danh_muc || categories[0]?.id || 1,
          don_gia: Number(editingFood.don_gia || 50000),
          con_hang: editingFood.con_hang ?? true,
          hien_thi: editingFood.hien_thi ?? true,
        });
      }
      setFoodModalOpen(false);
      setEditingFood(null);
      fetchData();
    } catch (err) {
      alert("Lỗi khi lưu món ăn.");
    }
  };

  const handleDeleteFood = async (slug: string) => {
    if (!confirm("Bạn có chắc chắn muốn xóa món này?")) return;
    try {
      await deleteAdminFood(slug);
      fetchData();
    } catch (err) {
      alert("Không thể xóa món ăn.");
    }
  };

  const handleSaveTransaction = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createInventoryTransaction(txData);
      setTxModalOpen(false);
      fetchData();
      alert("Đã cập nhật kho thành công!");
    } catch (err) {
      alert("Lỗi khi ghi nhận xuất nhập kho.");
    }
  };

  const filteredFoods = useMemo(() => {
    return foods.filter((f) => {
      const matchCat = catFilter === "all" || String(f.danh_muc) === catFilter;
      const matchSearch =
        !searchQuery ||
        f.ten.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.mo_ta_ngan?.toLowerCase().includes(searchQuery.toLowerCase());
      return matchCat && matchSearch;
    });
  }, [foods, catFilter, searchQuery]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Quản lý Thực đơn & Kho nguyên liệu</h1>
          <p className="text-sm text-gray-500">Quản lý danh sách món ăn, định mức và luồng xuất nhập nguyên liệu.</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={fetchData} className="p-2 border rounded-lg hover:bg-gray-100" title="Làm mới">
            <RefreshCw className="w-4 h-4" />
          </button>
          <div className="flex bg-gray-200 p-1 rounded-lg text-sm">
            <button
              onClick={() => setActiveTab("foods")}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === "foods" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Món ăn ({foods.length})
            </button>
            <button
              onClick={() => setActiveTab("ingredients")}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === "ingredients" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Kho nguyên liệu ({ingredients.length})
            </button>
            <button
              onClick={() => setActiveTab("transactions")}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === "transactions" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Lịch sử kho ({transactions.length})
            </button>
          </div>
        </div>
      </div>

      {/* TAB 1: FOOD CATALOG */}
      {activeTab === "foods" && (
        <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
          <div className="p-4 border-b flex flex-col md:flex-row gap-3 justify-between">
            <div className="flex flex-1 gap-2">
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                <input
                  type="text"
                  placeholder="Tìm món theo tên hoặc mô tả..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <select
                value={catFilter}
                onChange={(e) => setCatFilter(e.target.value)}
                className="px-3 py-2 border rounded-lg text-sm bg-white"
              >
                <option value="all">Tất cả danh mục</option>
                {categories.map((c) => (
                  <option key={c.id} value={String(c.id)}>{c.ten}</option>
                ))}
              </select>
            </div>
            <button
              onClick={() => {
                setEditingFood({
                  ten: "",
                  don_gia: 60000,
                  danh_muc: categories[0]?.id || 1,
                  con_hang: true,
                  hien_thi: true,
                  la_mon_chay: false,
                  do_cay: 0,
                  mo_ta_ngan: "",
                });
                setFoodModalOpen(true);
              }}
              className="flex items-center gap-1.5 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary/90"
            >
              <Plus className="w-4 h-4" /> Thêm món mới
            </button>
          </div>

          {loading ? (
            <div className="p-12 text-center text-gray-500">Đang tải danh sách món...</div>
          ) : filteredFoods.length === 0 ? (
            <div className="p-12 text-center text-gray-400">Không tìm thấy món ăn nào.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-50 border-b text-gray-600 font-medium">
                  <tr>
                    <th className="p-3.5">Tên món</th>
                    <th className="p-3.5">Danh mục</th>
                    <th className="p-3.5">Đơn giá</th>
                    <th className="p-3.5">Đặc trưng</th>
                    <th className="p-3.5">Còn hàng</th>
                    <th className="p-3.5">Hiển thị</th>
                    <th className="p-3.5 text-right">Hành động</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredFoods.map((f) => (
                    <tr key={f.id} className="hover:bg-gray-50/70 transition-colors">
                      <td className="p-3.5">
                        <div className="font-semibold text-gray-900">{f.ten}</div>
                        <div className="text-xs text-gray-400 truncate max-w-xs">{f.mo_ta_ngan}</div>
                      </td>
                      <td className="p-3.5 text-gray-600">
                        {categories.find((c) => c.id === f.danh_muc)?.ten || f.chi_tiet_danh_muc?.ten || "Khác"}
                      </td>
                      <td className="p-3.5 font-medium text-gray-900">{Number(f.don_gia).toLocaleString()}đ</td>
                      <td className="p-3.5">
                        <div className="flex gap-1 text-xs">
                          {f.la_mon_chay && <span className="px-1.5 py-0.5 bg-green-100 text-green-700 rounded">Chay</span>}
                          {f.do_cay > 0 && <span className="px-1.5 py-0.5 bg-red-100 text-red-700 rounded">🌶️ x{f.do_cay}</span>}
                          {f.noi_bat && <span className="px-1.5 py-0.5 bg-amber-100 text-amber-800 rounded">⭐ Nổi bật</span>}
                        </div>
                      </td>
                      <td className="p-3.5">
                        <button
                          onClick={() => handleToggleFoodStatus(f, "con_hang")}
                          className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                            f.con_hang ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"
                          }`}
                        >
                          {f.con_hang ? "Còn hàng" : "Hết hàng"}
                        </button>
                      </td>
                      <td className="p-3.5">
                        <button
                          onClick={() => handleToggleFoodStatus(f, "hien_thi")}
                          className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                            f.hien_thi ? "bg-blue-100 text-blue-800" : "bg-gray-100 text-gray-600"
                          }`}
                        >
                          {f.hien_thi ? "Hiển thị" : "Đã ẩn"}
                        </button>
                      </td>
                      <td className="p-3.5 text-right space-x-1">
                        <button
                          onClick={() => {
                            setEditingFood(f);
                            setFoodModalOpen(true);
                          }}
                          className="p-1.5 text-gray-500 hover:text-primary rounded hover:bg-gray-100"
                          title="Sửa"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteFood(f.duong_dan)}
                          className="p-1.5 text-gray-500 hover:text-red-600 rounded hover:bg-gray-100"
                          title="Xóa"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: INGREDIENTS */}
      {activeTab === "ingredients" && (
        <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
          <div className="p-4 border-b flex justify-between items-center">
            <h3 className="font-bold text-gray-800">Kho nguyên liệu thực phẩm</h3>
            <button
              onClick={() => setTxModalOpen(true)}
              className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm hover:bg-emerald-700"
            >
              <Package className="w-4 h-4" /> Nhập / Xuất kho
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 border-b text-gray-600 font-medium">
                <tr>
                  <th className="p-3.5">Tên nguyên liệu</th>
                  <th className="p-3.5">Đơn vị</th>
                  <th className="p-3.5">Tồn kho hiện tại</th>
                  <th className="p-3.5">Mức tối thiểu</th>
                  <th className="p-3.5">Tình trạng cảnh báo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {ingredients.map((ing) => {
                  const isLow = Number(ing.ton_kho_hien_tai) <= Number(ing.ton_kho_toi_thieu);
                  return (
                    <tr key={ing.id} className="hover:bg-gray-50/70 transition-colors">
                      <td className="p-3.5 font-semibold text-gray-900">{ing.ten}</td>
                      <td className="p-3.5 text-gray-600">{ing.don_vi}</td>
                      <td className="p-3.5 font-bold text-gray-900">{Number(ing.ton_kho_hien_tai).toFixed(1)}</td>
                      <td className="p-3.5 text-gray-500">{Number(ing.ton_kho_toi_thieu).toFixed(1)}</td>
                      <td className="p-3.5">
                        {isLow ? (
                          <span className="flex items-center gap-1 text-xs text-red-600 font-semibold bg-red-50 px-2.5 py-1 rounded-full w-fit">
                            <AlertTriangle className="w-3.5 h-3.5" /> Sắp hết hàng
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-xs text-emerald-700 font-medium bg-emerald-50 px-2.5 py-1 rounded-full w-fit">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Đủ hàng
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: TRANSACTIONS */}
      {activeTab === "transactions" && (
        <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
          <div className="p-4 border-b">
            <h3 className="font-bold text-gray-800">Lịch sử xuất nhập điều chỉnh kho</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 border-b text-gray-600 font-medium">
                <tr>
                  <th className="p-3.5">Thời gian</th>
                  <th className="p-3.5">Nguyên liệu</th>
                  <th className="p-3.5">Loại giao dịch</th>
                  <th className="p-3.5">Số lượng</th>
                  <th className="p-3.5">Trước → Sau</th>
                  <th className="p-3.5">Ghi chú</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {transactions.map((tx) => {
                  const ing = ingredients.find((i) => i.id === tx.nguyen_lieu);
                  const isNhap = tx.loai_giao_dich === "nhap";
                  return (
                    <tr key={tx.id} className="hover:bg-gray-50/70 transition-colors">
                      <td className="p-3.5 text-xs text-gray-500">{new Date(tx.tao_luc).toLocaleString()}</td>
                      <td className="p-3.5 font-medium text-gray-900">{ing?.ten || `Nguyên liệu #${tx.nguyen_lieu}`}</td>
                      <td className="p-3.5">
                        <span
                          className={`px-2 py-0.5 text-xs rounded font-medium ${
                            isNhap ? "bg-green-100 text-green-800" : "bg-orange-100 text-orange-800"
                          }`}
                        >
                          {isNhap ? "Nhập kho" : tx.loai_giao_dich === "xuat" ? "Xuất kho" : "Điều chỉnh"}
                        </span>
                      </td>
                      <td className="p-3.5 font-bold">
                        {isNhap ? "+" : "-"}{Number(tx.so_luong).toFixed(1)} {ing?.don_vi}
                      </td>
                      <td className="p-3.5 text-xs text-gray-600">
                        {Number(tx.ton_kho_truoc).toFixed(1)} → {Number(tx.ton_kho_sau).toFixed(1)}
                      </td>
                      <td className="p-3.5 text-xs text-gray-500">{tx.ghi_chu || "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* FOOD MODAL */}
      {foodModalOpen && editingFood && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <form onSubmit={handleSaveFood} className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="font-bold text-lg border-b pb-3">
              {editingFood.duong_dan ? "Chỉnh sửa món ăn" : "Thêm món ăn mới"}
            </h3>
            <div className="space-y-3 text-sm">
              <div>
                <label className="block text-xs font-semibold mb-1">Tên món ăn:</label>
                <input
                  type="text"
                  required
                  value={editingFood.ten || ""}
                  onChange={(e) => setEditingFood({ ...editingFood, ten: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold mb-1">Đơn giá (VNĐ):</label>
                  <input
                    type="number"
                    min="0"
                    step="1000"
                    required
                    value={editingFood.don_gia || 0}
                    onChange={(e) => setEditingFood({ ...editingFood, don_gia: Number(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1">Danh mục:</label>
                  <select
                    value={editingFood.danh_muc || categories[0]?.id}
                    onChange={(e) => setEditingFood({ ...editingFood, danh_muc: Number(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg bg-white"
                  >
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>{c.ten}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Mô tả ngắn:</label>
                <textarea
                  rows={2}
                  value={editingFood.mo_ta_ngan || ""}
                  onChange={(e) => setEditingFood({ ...editingFood, mo_ta_ngan: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div className="flex gap-4">
                <label className="flex items-center gap-1.5 text-xs cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editingFood.la_mon_chay || false}
                    onChange={(e) => setEditingFood({ ...editingFood, la_mon_chay: e.target.checked })}
                    className="rounded text-primary"
                  />
                  Món chay
                </label>
                <label className="flex items-center gap-1.5 text-xs cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editingFood.noi_bat || false}
                    onChange={(e) => setEditingFood({ ...editingFood, noi_bat: e.target.checked })}
                    className="rounded text-primary"
                  />
                  Nổi bật
                </label>
              </div>
            </div>
            <div className="pt-3 border-t flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setFoodModalOpen(false)}
                className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-100"
              >
                Hủy
              </button>
              <button type="submit" className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90">
                Lưu
              </button>
            </div>
          </form>
        </div>
      )}

      {/* TRANSACTION MODAL */}
      {txModalOpen && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <form onSubmit={handleSaveTransaction} className="bg-white rounded-xl shadow-xl max-w-sm w-full p-6 space-y-4">
            <h3 className="font-bold text-lg border-b pb-3">Xuất / Nhập nguyên liệu kho</h3>
            <div className="space-y-3 text-sm">
              <div>
                <label className="block text-xs font-semibold mb-1">Chọn nguyên liệu:</label>
                <select
                  value={txData.nguyen_lieu}
                  onChange={(e) => setTxData({ ...txData, nguyen_lieu: Number(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg bg-white"
                >
                  {ingredients.map((i) => (
                    <option key={i.id} value={i.id}>{i.ten} (Đơn vị: {i.don_vi})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Loại giao dịch:</label>
                <select
                  value={txData.loai_giao_dich}
                  onChange={(e) => setTxData({ ...txData, loai_giao_dich: e.target.value as any })}
                  className="w-full px-3 py-2 border rounded-lg bg-white"
                >
                  <option value="nhap">Nhập kho (+)</option>
                  <option value="xuat">Xuất kho (-)</option>
                  <option value="dieu_chinh">Điều chỉnh kiểm kê</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Số lượng:</label>
                <input
                  type="number"
                  min="0.1"
                  step="0.1"
                  required
                  value={txData.so_luong}
                  onChange={(e) => setTxData({ ...txData, so_luong: Number(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Ghi chú:</label>
                <input
                  type="text"
                  placeholder="Nhập kho buổi sáng, chế biến..."
                  value={txData.ghi_chu}
                  onChange={(e) => setTxData({ ...txData, ghi_chu: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>
            <div className="pt-3 border-t flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setTxModalOpen(false)}
                className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-100"
              >
                Hủy
              </button>
              <button type="submit" className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700">
                Xác nhận
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
