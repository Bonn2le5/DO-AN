import { Users } from "lucide-react";
import { cn, localDateInputValue } from "@/lib/utils";
import TablePicker from "./TablePicker";
import HoldCountdown from "./HoldCountdown";
import type { RestaurantTable } from "@/types";

const TIME_SLOTS = [
  "11:00",
  "11:30",
  "12:00",
  "12:30",
  "18:00",
  "18:30",
  "19:00",
  "19:30",
  "20:00",
];

interface TableStepProps {
  date: string;
  onDateChange: (v: string) => void;
  time: string;
  onTimeChange: (v: string) => void;
  partySize: number;
  onPartySizeChange: (v: number) => void;
  tables: RestaurantTable[];
  tablesLoading: boolean;
  selectedTableId: string | null;
  holdLoading: boolean;
  holdError: string;
  holdInfo: { holdId: string; heldUntil: string } | null;
  onSelectTable: (id: string) => void;
  onContinue: () => void;
}

export default function TableStep({
  date,
  onDateChange,
  time,
  onTimeChange,
  partySize,
  onPartySizeChange,
  tables,
  tablesLoading,
  selectedTableId,
  holdLoading,
  holdError,
  holdInfo,
  onSelectTable,
  onContinue,
}: TableStepProps) {
  return (
    <div className="space-y-8">
      <div className="grid sm:grid-cols-3 gap-4">
        <div>
          <label className="text-sm font-bold uppercase tracking-wide text-muted block mb-2">
            Ngày
          </label>
          <input
            type="date"
            value={date}
            min={localDateInputValue()}
            onChange={(e) => onDateChange(e.target.value)}
            className="w-full px-4 py-3 rounded-xl border border-black/15 text-sm outline-none focus:border-primary"
          />
        </div>
        <div>
          <label className="text-sm font-bold uppercase tracking-wide text-muted block mb-2">
            Số khách
          </label>
          <div className="flex items-center gap-2 border border-black/15 rounded-xl px-3 py-2.5">
            <Users width={16} height={16} className="text-muted" />
            <input
              type="number"
              min={1}
              max={12}
              value={partySize}
              onChange={(e) => onPartySizeChange(Number(e.target.value))}
              className="w-full outline-none text-sm"
            />
          </div>
        </div>
      </div>

      <div>
        <label className="text-sm font-bold uppercase tracking-wide text-muted block mb-3">
          Khung giờ
        </label>
        <div className="flex flex-wrap gap-2.5">
          {TIME_SLOTS.map((slot) => (
            <button
              key={slot}
              type="button"
              onClick={() => onTimeChange(slot)}
              className={cn(
                "px-4 py-2.5 rounded-full text-sm font-medium border-[1.5px] transition-colors",
                time === slot
                  ? "bg-dark text-white border-dark"
                  : "border-black/15 hover:border-dark",
              )}
            >
              {slot}
            </button>
          ))}
        </div>
      </div>

      {tablesLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-20 rounded-xl bg-black/5 animate-pulse" />
          ))}
        </div>
      ) : (
        <TablePicker
          tables={tables}
          partySize={partySize}
          selectedTable={selectedTableId}
          onSelect={onSelectTable}
        />
      )}

      {holdError && <p className="text-sm text-primary">{holdError}</p>}
      {holdLoading && <p className="text-sm text-muted">Đang giữ bàn...</p>}

      {holdInfo && !holdLoading && (
        <div className="flex items-center justify-between flex-wrap gap-3 bg-accent/5 border border-accent/20 rounded-xl px-4 py-3.5">
          <div className="text-sm">
            Bàn đã được <strong>giữ tạm</strong>. Hoàn tất đặt bàn trước khi hết
            giờ để không bị nhả bàn cho khách khác.
          </div>
          <HoldCountdown until={holdInfo.heldUntil} label="Còn lại" />
        </div>
      )}

      <button
        onClick={onContinue}
        disabled={!selectedTableId || holdLoading}
        className="btn btn-primary w-full disabled:opacity-40"
      >
        Tiếp tục
      </button>
    </div>
  );
}
