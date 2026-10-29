import { cn } from "@/lib/utils";
import type { RestaurantTable } from "@/types";

const STATUS_STYLE: Record<RestaurantTable["status"], string> = {
  available: "border-black/15 hover:border-primary cursor-pointer",
  held: "border-accent/40 bg-accent/5 opacity-70 cursor-not-allowed",
  reserved: "border-black/10 bg-black/[0.03] opacity-50 cursor-not-allowed",
  occupied: "border-black/10 bg-black/[0.03] opacity-50 cursor-not-allowed",
  maintenance: "border-black/10 bg-black/[0.03] opacity-40 cursor-not-allowed",
};

const STATUS_LABEL: Record<RestaurantTable["status"], string> = {
  available: "Còn trống",
  held: "Đang được giữ",
  reserved: "Đã đặt",
  occupied: "Đang sử dụng",
  maintenance: "Bảo trì",
};

interface TablePickerProps {
  tables: RestaurantTable[];
  partySize: number;
  selectedTable: string | null;
  onSelect: (tableId: string) => void;
}

export default function TablePicker({ tables, partySize, selectedTable, onSelect }: TablePickerProps) {
  const availableTables = tables.filter((t) => t.capacity >= partySize);

  return (
    <div>
      <label className="text-sm font-bold uppercase tracking-wide text-muted block mb-3">
        Chọn bàn ({availableTables.length} bàn phù hợp với {partySize} khách)
      </label>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {availableTables.map((table) => (
          <button
            key={table.id}
            type="button"
            disabled={table.status !== "available"}
            onClick={() => onSelect(table.id)}
            className={cn(
              "rounded-xl border-[1.5px] p-4 text-left transition-colors",
              table.status === "available"
                ? selectedTable === table.id
                  ? "border-primary bg-primary/5"
                  : STATUS_STYLE.available
                : STATUS_STYLE[table.status]
            )}
          >
            <div className="font-semibold text-sm">{table.label}</div>
            <div className="text-xs text-muted mt-1">
              {table.zone} · {table.capacity} khách
            </div>
            <div className={cn("text-[11px] font-semibold mt-2", table.status === "available" ? "text-success" : "text-muted")}>
              {STATUS_LABEL[table.status]}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
