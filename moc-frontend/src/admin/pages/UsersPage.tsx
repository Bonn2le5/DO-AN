import CrudPage from "../components/CrudPage";
import { StatusBadge } from "../components/primitives";
import { usersStore } from "../api/admin.api";
import { fmtDateTime } from "../lib";
import type { AdminUser } from "../data/mockCatalog";

const ROLE = { admin: { label: "Quản trị viên", tone: "dark" }, staff: { label: "Nhân viên", tone: "info" }, customer: { label: "Khách hàng", tone: "neutral" } } as const;

export default function UsersPage() {
  return (
    <CrudPage<AdminUser>
      title="Người dùng" noun="người dùng" module="users" store={usersStore}
      subtitle="Khoá tài khoản thay vì xoá để giữ lịch sử đơn hàng."
      blank={{ name: "", email: "", phone: "", role: "customer", active: true, createdAt: new Date().toISOString(), password: "" }}
      searchText={(u) => `${u.name} ${u.email} ${u.phone}`} quickToggle={{ key: "active", header: "Hoạt động" }}
      columns={[
        { header: "Người dùng", cell: (u) => <div><div className="font-semibold">{u.name}</div><div className="text-xs text-muted">{u.email}</div></div> },
        { header: "Điện thoại", cell: (u) => u.phone },
        { header: "Vai trò", cell: (u) => <StatusBadge tone={ROLE[u.role].tone}>{ROLE[u.role].label}</StatusBadge> },
        { header: "Tham gia", cell: (u) => fmtDateTime(u.createdAt) },
      ]}
      fields={[
        { key: "name", label: "Họ và tên", type: "text", required: true },
        { key: "email", label: "Email", type: "text", required: true },
        { key: "phone", label: "Điện thoại", type: "text" },
        { key: "password", label: "Mật khẩu khởi tạo", type: "password", hint: "Bắt buộc khi tạo tài khoản mới; bỏ trống khi sửa." },
        { key: "role", label: "Vai trò", type: "select", required: true, options: [{ value: "customer", label: "Khách hàng" }, { value: "staff", label: "Nhân viên" }, { value: "admin", label: "Quản trị viên" }] },
        { key: "active", label: "Tài khoản đang hoạt động", type: "toggle" },
      ]}
    />
  );
}
