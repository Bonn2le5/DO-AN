import { useMemo, useState, type ReactNode } from "react";
import { Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import type { Store } from "../api/store";
import { useCan } from "../permissions";
import type { Module } from "../types";
import DataTable, { type Column } from "./DataTable";
import RecordDrawer, { type FieldDef } from "./RecordDrawer";
import ConfirmModal from "./ConfirmModal";
import { PageHeader, Toggle, inputCls } from "./primitives";
import { useToast } from "./toast";

interface CrudPageProps<T extends { id: string }> {
  title: string;
  subtitle?: string;
  noun: string;
  module: Module;
  store: Store<T>;
  columns: Column<T>[];
  fields: FieldDef<T>[];
  blank: Omit<T, "id">;
  searchText?: (row: T) => string;
  quickToggle?: { key: keyof T & string; header: string };
  rowActions?: (row: T, reload: () => void) => ReactNode;
  headerActions?: ReactNode;
  hideHeader?: boolean;
  hideAdd?: boolean;
  hideDelete?: boolean;
}

export default function CrudPage<T extends { id: string }>({
  title, subtitle, noun, module, store, columns, fields, blank, searchText, quickToggle, rowActions, headerActions, hideHeader, hideAdd, hideDelete,
}: CrudPageProps<T>) {
  const can = useCan();
  const push = useToast((s) => s.push);
  const { data, loading, refetch } = useAsync(() => store.list(), [store]);
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState<T | "new" | null>(null);
  const [deleting, setDeleting] = useState<T | null>(null);
  const [busy, setBusy] = useState(false);

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q && searchText ? data?.filter((r) => searchText(r).toLowerCase().includes(q)) : data;
  }, [data, query, searchText]);

  const initial = useMemo(() => (editing === "new" || editing === null ? (blank as Partial<T>) : (editing as Partial<T>)), [editing, blank]);

  const save = async (values: Partial<T>) => {
    setBusy(true);
    try {
      if (editing === "new") await store.create(values as Omit<T, "id">);
      else if (editing) await store.update(editing.id, values);
      push(editing === "new" ? `Đã thêm ${noun}` : `Đã lưu ${noun}`);
      setEditing(null);
      refetch();
    } catch (e) {
      push(e instanceof Error ? e.message : "Không lưu được, vui lòng thử lại", "err");
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (!deleting) return;
    setBusy(true);
    try {
      await store.remove(deleting.id);
      push(`Đã xoá ${noun}`);
      setDeleting(null);
      refetch();
    } catch {
      push(`Không xoá được ${noun}. Có thể đang được dùng ở nơi khác.`, "err");
    } finally {
      setBusy(false);
    }
  };

  const toggleQuick = async (row: T, value: boolean) => {
    if (!quickToggle) return;
    await store.update(row.id, { [quickToggle.key]: value } as Partial<T>);
    refetch();
  };

  const allColumns: Column<T>[] = [
    ...columns,
    ...(quickToggle
      ? [{ header: quickToggle.header, cell: (r: T) => <Toggle label={quickToggle.header} checked={!!r[quickToggle.key]} disabled={!can(module, "update")} onChange={(v) => toggleQuick(r, v)} /> }]
      : []),
    {
      header: "", className: "text-right whitespace-nowrap",
      cell: (r) => (
        <div className="flex justify-end gap-1" onClick={(e) => e.stopPropagation()}>
          {rowActions?.(r, refetch)}
          {can(module, "update") && <button className="icon-btn w-8! h-8!" aria-label={`Sửa ${noun}`} onClick={() => setEditing(r)}><Pencil width={15} height={15} /></button>}
          {!hideDelete && can(module, "delete") && <button className="icon-btn w-8! h-8! hover:text-primary" aria-label={`Xoá ${noun}`} onClick={() => setDeleting(r)}><Trash2 width={15} height={15} /></button>}
        </div>
      ),
    },
  ];

  const addButton = !hideAdd && can(module, "create") && (
    <button className="btn btn-primary py-2.5! px-5! text-sm!" onClick={() => setEditing("new")}><Plus width={16} height={16} />Thêm {noun}</button>
  );

  return (
    <div>
      {!hideHeader && <PageHeader title={title} subtitle={subtitle} actions={<>{headerActions}{addButton}</>} />}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        {searchText && (
          <div className="relative w-full sm:w-72">
            <Search width={15} height={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" />
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder={`Tìm ${noun}…`} aria-label={`Tìm ${noun}`} className={`${inputCls} pl-9`} />
          </div>
        )}
        {hideHeader && <div className="ml-auto">{addButton}</div>}
      </div>
      <DataTable
        columns={allColumns} rows={rows} loading={loading}
        onRowClick={can(module, "update") ? (r) => setEditing(r) : undefined}
        emptyTitle={query ? "Không tìm thấy kết quả" : `Chưa có ${noun}`}
        emptyHint={query ? "Thử từ khoá khác." : can(module, "create") ? `Bấm “Thêm ${noun}” để tạo mới.` : undefined}
      />
      <RecordDrawer<T>
        open={editing !== null} title={editing === "new" ? `Thêm ${noun}` : `Sửa ${noun}`}
        fields={fields} initial={initial} saving={busy} onClose={() => setEditing(null)} onSave={save}
      />
      <ConfirmModal
        open={!!deleting} danger busy={busy} title={`Xoá ${noun}?`} confirmLabel="Xoá"
        message="Thao tác này không thể hoàn tác." onConfirm={remove} onCancel={() => setDeleting(null)}
      />
    </div>
  );
}
