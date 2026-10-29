export default function AdminDashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Tổng quan</h1>
        <p className="text-gray-500">Xin chào, đây là trang tổng quan vận hành nhà hàng.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { title: "Đơn hàng hôm nay", value: "0", sub: "0 đơn đang chờ", color: "bg-blue-50 border-blue-200 text-blue-700" },
          { title: "Khách đặt bàn", value: "0", sub: "Hôm nay", color: "bg-green-50 border-green-200 text-green-700" },
          { title: "Doanh thu (ước tính)", value: "0 đ", sub: "Hôm nay", color: "bg-amber-50 border-amber-200 text-amber-700" },
          { title: "Phản hồi mới", value: "0", sub: "Chưa đọc", color: "bg-purple-50 border-purple-200 text-purple-700" },
        ].map((stat, i) => (
          <div key={i} className={`p-5 rounded-xl border ${stat.color}`}>
            <h3 className="text-sm font-medium opacity-80">{stat.title}</h3>
            <div className="mt-2 text-3xl font-bold">{stat.value}</div>
            <p className="mt-1 text-xs opacity-80">{stat.sub}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl border shadow-sm h-80 flex items-center justify-center">
          <p className="text-gray-400">Biểu đồ đang cập nhật...</p>
        </div>
        <div className="bg-white p-6 rounded-xl border shadow-sm h-80 flex flex-col">
          <h3 className="font-semibold mb-4">Hoạt động gần đây</h3>
          <div className="flex-1 flex items-center justify-center text-gray-400">
            Chưa có hoạt động nào
          </div>
        </div>
      </div>
    </div>
  );
}