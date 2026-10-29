import { useEffect, useState } from "react";
import { Lock } from "lucide-react";
import { ACTIONS, MATRIX, MODULES } from "../permissions";
import { PageHeader, Tabs } from "../components/primitives";
import { useToast } from "../components/toast";
import type { Action, Module, RoleName } from "../types";
import { getRolePermissions, saveRolePermissions } from "../api/admin.api";

type Matrix = Record<RoleName, Partial<Record<Module, Action[]>>>;

/** TODO(backend): lưu qua POST /api/roles/{id}/permissions/ (bảng role_permissions). Hiện chỉ chỉnh trên giao diện. */
export default function RolesPage() {
  const push = useToast((s) => s.push);
  const [role, setRole] = useState<RoleName>("staff");
  const [matrix, setMatrix] = useState<Matrix>(() => structuredClone(MATRIX));
  const [saving, setSaving] = useState(false);
  const locked = role === "admin";

  useEffect(() => {
    if (locked) return;
    void getRolePermissions(role).then((permissions) => {
      const hasAny = Object.values(permissions as Record<string, string[]>).some((actions) => actions.length > 0);
      if (!hasAny) return;
      setMatrix((prev) => ({ ...prev, [role]: permissions as Partial<Record<Module, Action[]>> }));
    }).catch((e) => push(e instanceof Error ? e.message : "Không tải được phân quyền", "err"));
  }, [role, locked, push]);

  const save = async () => {
    setSaving(true);
    try { await saveRolePermissions(role, matrix[role] as Record<string, string[]>); push("Đã lưu phân quyền"); }
    catch (e) { push(e instanceof Error ? e.message : "Không lưu được phân quyền", "err"); }
    finally { setSaving(false); }
  };

  const toggle = (m: Module, a: Action) =>
    setMatrix((prev) => {
      const cur = prev[role][m] ?? [];
      const next = cur.includes(a) ? cur.filter((x) => x !== a) : [...cur, a];
      return { ...prev, [role]: { ...prev[role], [m]: next } };
    });

  return (
    <div className="max-w-3xl">
      <PageHeader
        title="Vai trò & quyền" subtitle="Chọn quyền cho từng vai trò. Giao diện chỉ ẩn/hiện chức năng; máy chủ mới là nơi kiểm tra quyền thật."
        actions={!locked && <button className="btn btn-primary py-2.5! px-5! text-sm!" disabled={saving} onClick={save}>{saving ? "Đang lưu..." : "Lưu phân quyền"}</button>}
      />
      <div className="mb-4"><Tabs value={role} onChange={setRole} items={[{ key: "staff", label: "Nhân viên" }, { key: "admin", label: "Quản trị viên" }]} /></div>
      {locked && <p className="flex items-center gap-2 text-sm text-muted mb-3"><Lock width={14} height={14} />Quản trị viên luôn có toàn quyền, không chỉnh được.</p>}
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr className="text-left text-[13px] text-muted border-b border-black/[0.07] bg-black/2">
            <th className="px-4 py-3 font-semibold">Chức năng</th>
            {ACTIONS.map((a) => <th key={a.key} className="px-4 py-3 font-semibold text-center">{a.label}</th>)}
          </tr></thead>
          <tbody>
            {MODULES.map((m) => (
              <tr key={m.key} className="border-b border-black/5 last:border-0">
                <td className="px-4 py-2.5 font-medium">{m.label}</td>
                {ACTIONS.map((a) => (
                  <td key={a.key} className="px-4 py-2.5 text-center">
                    <input
                      type="checkbox" className="w-4 h-4 accent-primary" disabled={locked} aria-label={`${m.label}: ${a.label}`}
                      checked={!!matrix[role][m.key]?.includes(a.key)} onChange={() => toggle(m.key, a.key)}
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
