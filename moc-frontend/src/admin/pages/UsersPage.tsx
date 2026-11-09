import CrudPage from "../components/CrudPage";
import { StatusBadge } from "../components/primitives";
import { usersStore } from "../api/admin.api";
import { fmtDateTime } from "../lib";
import type { AdminUser } from "../data/mockCatalog";
import { useAsync } from "@/hooks/useAsync";
import { branchesStore } from "../api/admin.api";
import { useRole } from "../permissions";
import { useAuthStore } from "@/store/authStore";

const ROLE = { admin: { label: "Quản trị toàn hệ thống", tone: "dark" }, branch_manager: { label: "Quản lý chi nhánh", tone: "info" }, staff: { label: "Nhân viên", tone: "warn" }, customer: { label: "Khách hàng", tone: "neutral" } } as const;

export default function UsersPage() {
  const { data: branches } = useAsync(() => branchesStore.list());
  const branchOptions = (branches ?? []).map((b) => ({ value: b.id, label: b.name }));
  // Quản lý chi nhánh chỉ quản lý nhân viên bán hàng của chi nhánh mình: không chọn vai trò hay chi nhánh.
  const isManager = useRole() === "branch_manager";
  const myBranch = useAuthStore((s) => s.nguoiDung?.idChiNhanh) ?? "";
  if (isManager) {
    return (
      <CrudPage<AdminUser>
        title="Nhân viên chi nhánh" noun="nhân viên" module="users" store={usersStore} hideDelete
        subtitle={`Tài khoản nhân viên bán hàng của ${branchOptions.find((b) => b.value === myBranch)?.label ?? "chi nhánh"}. Nhân viên nghỉ việc thì khoá tài khoản, không xoá.`}
        blank={{ name: "", email: "", phone: "", role: "staff", active: true, createdAt: new Date().toISOString(), password: "", branchId: myBranch }}
        searchText={(u) => `${u.name} ${u.email} ${u.phone}`} quickToggle={{ key: "active", header: "Đang làm" }}
        columns={[
          { header: "Nhân viên", cell: (u) => <div><div className="font-semibold">{u.name}</div><div className="text-xs text-muted">{u.email}</div></div> },
          { header: "Điện thoại", cell: (u) => u.phone },
          { header: "Tham gia", cell: (u) => fmtDateTime(u.createdAt) },
        ]}
        fields={[
          { key: "name", label: "Họ và tên", type: "text", required: true },
          { key: "email", label: "Email đăng nhập", type: "email", required: true },
          { key: "phone", label: "Điện thoại", type: "text" },
          { key: "password", label: "Mật khẩu", type: "password", requiredWhen: (values) => !values.id, minLength: 8, hint: "Bắt buộc khi tạo mới, tối thiểu 8 ký tự. Khi sửa: nhập để đặt lại mật khẩu, bỏ trống để giữ nguyên." },
          { key: "active", label: "Tài khoản đang hoạt động", type: "toggle" },
        ]}
      />
    );
  }
  return (
    <CrudPage<AdminUser>
      title="Người dùng" noun="người dùng" module="users" store={usersStore}
      subtitle="Khoá tài khoản thay vì xoá để giữ lịch sử đơn hàng."
      blank={{ name: "", email: "", phone: "", role: "customer", active: true, createdAt: new Date().toISOString(), password: "", branchId: "" }}
      searchText={(u) => `${u.name} ${u.email} ${u.phone}`} quickToggle={{ key: "active", header: "Hoạt động" }}
      columns={[
        { header: "Người dùng", cell: (u) => <div><div className="font-semibold">{u.name}</div><div className="text-xs text-muted">{u.email}</div></div> },
        { header: "Điện thoại", cell: (u) => u.phone },
        { header: "Vai trò", cell: (u) => <StatusBadge tone={ROLE[u.role].tone}>{ROLE[u.role].label}</StatusBadge> },
        { header: "Chi nhánh phụ trách", cell: (u) => branchOptions.find((b) => b.value === u.branchId)?.label ?? (u.role === "admin" ? "Toàn hệ thống" : "Chưa gán") },
        { header: "Tham gia", cell: (u) => fmtDateTime(u.createdAt) },
      ]}
      fields={[
        { key: "name", label: "Họ và tên", type: "text", required: true },
        { key: "email", label: "Email", type: "email", required: true },
        { key: "phone", label: "Điện thoại", type: "text" },
        { key: "password", label: "Mật khẩu khởi tạo", type: "password", requiredWhen: (values) => !values.id, minLength: 8, hint: "Bắt buộc khi tạo tài khoản mới; tối thiểu 8 ký tự; bỏ trống khi sửa." },
        { key: "role", label: "Vai trò", type: "select", required: true, options: [{ value: "customer", label: "Khách hàng" }, { value: "staff", label: "Nhân viên" }, { value: "branch_manager", label: "Quản lý chi nhánh" }, { value: "admin", label: "Quản trị toàn hệ thống" }] },
        { key: "branchId", label: "Chi nhánh phụ trách", type: "select", requiredWhen: (values) => values.role === "staff" || values.role === "branch_manager", options: branchOptions, hint: "Bắt buộc với nhân viên và quản lý chi nhánh." },
        { key: "active", label: "Tài khoản đang hoạt động", type: "toggle" },
      ]}
    />
  );
}
