import { useState } from "react";
import { Lock } from "lucide-react";
import { ACTIONS, MATRIX, MODULES } from "../permissions";
import { PageHeader, Tabs } from "../components/primitives";
import type { RoleName } from "../types";

const ROLE_DESCRIPTION: Record<RoleName, string> = {
  admin: "Quản trị toàn hệ thống, xem và quản lý dữ liệu của cả ba chi nhánh.",
  branch_manager: "Quản lý đặt bàn, hóa đơn, đơn hàng và doanh thu trong chi nhánh được giao.",
  staff: "Quản lý đặt bàn, hóa đơn và đơn hàng trong chi nhánh được giao.",
};

export default function RolesPage() {
  const [role, setRole] = useState<RoleName>("staff");
  const permissions = MATRIX[role];

  return (
    <div className="max-w-3xl">
      <PageHeader title="Vai trò & quyền" subtitle="Quyền thao tác được giới hạn theo vai trò và chi nhánh phụ trách." />
      <div className="mb-4">
        <Tabs value={role} onChange={setRole} items={[
          { key: "staff", label: "Nhân viên" },
          { key: "branch_manager", label: "Quản lý chi nhánh" },
          { key: "admin", label: "Quản trị viên" },
        ]} />
      </div>
      <p className="flex items-center gap-2 text-sm text-muted mb-3">
        <Lock width={14} height={14} />{ROLE_DESCRIPTION[role]}
      </p>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr className="text-left text-[13px] text-muted border-b border-black/[0.07] bg-black/2">
            <th className="px-4 py-3 font-semibold">Chức năng</th>
            {ACTIONS.map((action) => <th key={action.key} className="px-4 py-3 font-semibold text-center">{action.label}</th>)}
          </tr></thead>
          <tbody>
            {MODULES.map((module) => (
              <tr key={module.key} className="border-b border-black/5 last:border-0">
                <td className="px-4 py-2.5 font-medium">{module.label}</td>
                {ACTIONS.map((action) => (
                  <td key={action.key} className="px-4 py-2.5 text-center">
                    <input
                      type="checkbox"
                      className="w-4 h-4 accent-primary"
                      disabled
                      checked={!!permissions[module.key]?.includes(action.key)}
                      aria-label={`${module.label}: ${action.label}`}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
