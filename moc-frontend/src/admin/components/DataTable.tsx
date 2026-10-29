import { useState, type ReactNode } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { EmptyState } from "./primitives";
import { cn } from "@/lib/utils";

export interface Column<T> {
  header: string;
  cell: (row: T) => ReactNode;
  className?: string;
}

interface DataTableProps<T extends { id: string }> {
  columns: Column<T>[];
  rows: T[] | undefined;
  loading?: boolean;
  onRowClick?: (row: T) => void;
  pageSize?: number;
  emptyTitle?: string;
  emptyHint?: string;
}

export default function DataTable<T extends { id: string }>({
  columns, rows, loading, onRowClick, pageSize = 10, emptyTitle = "Chưa có dữ liệu", emptyHint,
}: DataTableProps<T>) {
  const [page, setPage] = useState(0);
  const total = rows?.length ?? 0;
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const cur = Math.min(page, pages - 1);
  const visible = rows?.slice(cur * pageSize, cur * pageSize + pageSize) ?? [];

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-[13px] text-muted border-b border-black/[0.07] bg-black/2">
              {columns.map((c) => (<th key={c.header} className={cn("font-semibold px-4 py-3 whitespace-nowrap", c.className)}>{c.header}</th>))}
            </tr>
          </thead>
          <tbody>
            {loading
              ? Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="border-b border-black/5 last:border-0">
                    {columns.map((c) => (<td key={c.header} className="px-4 py-3.5"><div className="h-4 rounded bg-black/5 animate-pulse" /></td>))}
                  </tr>
                ))
              : visible.map((row) => (
                  <tr
                    key={row.id}
                    onClick={onRowClick ? () => onRowClick(row) : undefined}
                    className={cn("border-b border-black/5 last:border-0", onRowClick && "cursor-pointer hover:bg-black/2.5")}
                  >
                    {columns.map((c) => (<td key={c.header} className={cn("px-4 py-3 align-middle", c.className)}>{c.cell(row)}</td>))}
                  </tr>
                ))}
          </tbody>
        </table>
      </div>
      {!loading && total === 0 && <EmptyState title={emptyTitle} hint={emptyHint} />}
      {!loading && total > pageSize && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-black/[0.07] text-sm text-muted">
          <span>{cur * pageSize + 1}–{Math.min(total, (cur + 1) * pageSize)} / {total}</span>
          <div className="flex gap-1">
            <button className="icon-btn w-8! h-8!" disabled={cur === 0} onClick={() => setPage(cur - 1)} aria-label="Trang trước"><ChevronLeft width={16} height={16} /></button>
            <button className="icon-btn w-8! h-8!" disabled={cur >= pages - 1} onClick={() => setPage(cur + 1)} aria-label="Trang sau"><ChevronRight width={16} height={16} /></button>
          </div>
        </div>
      )}
    </div>
  );
}
