import { useEffect, useState } from "react";
import { MapPin, Phone, Clock, Users, Search } from "lucide-react";
import { cn, localDateInputValue } from "@/lib/utils";
import type { Branch } from "@/types";
import { layDanhSachChiNhanh, layKhungGioTrong } from "@/api/reservations.api";
import TablePicker from "./TablePicker";
import HoldCountdown from "./HoldCountdown";

interface BranchTimeStepProps {
  selectedBranchId: string;
  onBranchChange: (id: string) => void;
  date: string;
  onDateChange: (v: string) => void;
  partySize: number;
  onPartySizeChange: (v: number) => void;
  selectedTime: string;
  onTimeSelect: (time: string) => void;
  tables: import("@/types").RestaurantTable[];
  tablesLoading: boolean;
  selectedTableId: string | null;
  holdInfo: { holdId: string; heldUntil: string } | null;
  holdLoading: boolean;
  holdError: string;
  onSelectTable: (id: string) => void;
  onContinue: () => void;
}

export default function BranchTimeStep({
  selectedBranchId,
  onBranchChange,
  date,
  onDateChange,
  partySize,
  onPartySizeChange,
  selectedTime,
  onTimeSelect,
  tables,
  tablesLoading,
  selectedTableId,
  holdInfo,
  holdLoading,
  holdError,
  onSelectTable,
  onContinue,
}: BranchTimeStepProps) {
  const [branches, setBranches] = useState<Branch[]>([]);
  const [slots, setSlots] = useState<{ khungGio: string; conTrong: boolean }[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    layDanhSachChiNhanh().then(setBranches);
  }, []);

  const selectedBranch = branches.find((b) => b.id === selectedBranchId) ?? null;

  const handleSearch = async () => {
    if (!selectedBranchId || !date) return;
    setLoadingSlots(true);
    setSearched(true);
    try {
      const result = await layKhungGioTrong({
        chiNhanhId: selectedBranchId,
        ngay: date,
        soKhach: partySize,
      });
      setSlots(result);
    } finally {
      setLoadingSlots(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Search bar */}
      <div className="bg-white rounded-2xl border border-black/10 p-5 shadow-sm">
        <div className="grid sm:grid-cols-3 gap-4 mb-4">
          {/* Branch selector */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wide text-muted block mb-1.5">
              Chi nhánh
            </label>
            <select
              value={selectedBranchId}
              onChange={(e) => {
                onBranchChange(e.target.value);
                onTimeSelect("");
                setSearched(false);
              }}
              className="w-full px-3 py-3 rounded-xl border border-black/15 text-sm outline-none focus:border-primary bg-white"
            >
              <option value="">-- Chọn chi nhánh --</option>
              {branches.map((b) => (
                <option key={b.id} value={b.id}>
                  CN: {b.name}
                </option>
              ))}
            </select>
          </div>

          {/* Date */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wide text-muted block mb-1.5">
              Ngày đặt bàn
            </label>
            <input
              type="date"
              value={date}
              min={localDateInputValue()}
              onChange={(e) => {
                onDateChange(e.target.value);
                onTimeSelect("");
                setSearched(false);
              }}
              className="w-full px-3 py-3 rounded-xl border border-black/15 text-sm outline-none focus:border-primary"
            />
          </div>

          {/* Party size */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wide text-muted block mb-1.5">
              Số người
            </label>
            <div className="flex items-center gap-2 border border-black/15 rounded-xl px-3 py-2.5">
              <Users size={16} className="text-muted" />
              <input
                type="number"
                min={1}
                max={20}
                value={partySize}
                onChange={(e) => {
                  onPartySizeChange(Number(e.target.value));
                  onTimeSelect("");
                  setSearched(false);
                }}
                className="w-full outline-none text-sm"
              />
            </div>
          </div>
        </div>

        <button
          onClick={handleSearch}
          disabled={!selectedBranchId || !date || loadingSlots}
          className="w-full flex items-center justify-center gap-2 py-3 bg-primary text-white rounded-xl font-semibold hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          <Search size={18} />
          Tìm kiếm
        </button>
      </div>

      {/* Branch card + time slots */}
      {searched && selectedBranch && (
        <div className="rounded-2xl border border-black/10 overflow-hidden shadow-sm">
          <div className="grid md:grid-cols-[280px_1fr]">
            {/* Branch image placeholder */}
            <div className="bg-dark/5 hidden md:flex items-center justify-center min-h-[200px]">
              <MapPin size={48} className="text-muted/30" />
            </div>

            {/* Branch info + slots */}
            <div className="p-5 space-y-4">
              <div>
                <h3 className="font-bold text-lg">CN: {selectedBranch.name}</h3>
                <div className="mt-2 space-y-1.5 text-sm text-muted">
                  <div className="flex items-center gap-2">
                    <MapPin size={14} />
                    <span>{selectedBranch.address}</span>
                  </div>
                  {selectedBranch.phone && (
                    <div className="flex items-center gap-2">
                      <Phone size={14} />
                      <span>{selectedBranch.phone}</span>
                    </div>
                  )}
                  {selectedBranch.openHours && (
                    <div className="flex items-center gap-2">
                      <Clock size={14} />
                      <span>{selectedBranch.openHours}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Time slot grid */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold">Khung giờ còn trống:</span>
                  <div className="flex items-center gap-3 text-xs text-muted">
                    <span className="flex items-center gap-1">
                      <span className="w-3 h-3 rounded-sm bg-black/20 inline-block" />
                      Đã hết bàn
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-3 h-3 rounded-sm bg-primary inline-block" />
                      Còn bàn
                    </span>
                  </div>
                </div>

                {loadingSlots ? (
                  <div className="grid grid-cols-6 gap-1.5">
                    {Array.from({ length: 24 }).map((_, i) => (
                      <div key={i} className="h-9 rounded-lg bg-black/5 animate-pulse" />
                    ))}
                  </div>
                ) : (
                  slots.length === 0 ? (
                    <p className="text-sm text-muted py-4">Chưa tải được khung giờ. Vui lòng thử tìm lại.</p>
                  ) : (
                  <div className="grid grid-cols-5 sm:grid-cols-6 gap-1.5">
                    {slots.map((slot) => (
                      <button
                        key={slot.khungGio}
                        disabled={!slot.conTrong}
                        onClick={() => onTimeSelect(slot.khungGio)}
                        className={cn(
                          "py-2 px-1 rounded-lg text-xs font-semibold transition-all",
                          !slot.conTrong &&
                            "bg-black/10 text-muted/50 cursor-not-allowed",
                          slot.conTrong &&
                            selectedTime === slot.khungGio &&
                            "bg-dark text-white ring-2 ring-dark ring-offset-1",
                          slot.conTrong &&
                            selectedTime !== slot.khungGio &&
                            "bg-primary text-white hover:bg-primary/80"
                        )}
                      >
                        {slot.khungGio}
                      </button>
                    ))}
                  </div>
                  )
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {searched && selectedBranch && selectedTime && slots.some((slot) => slot.khungGio === selectedTime && slot.conTrong) && (
        <section className="card p-5 md:p-6">
          <h2 className="font-display text-xl mb-1">Chọn bàn</h2>
          <p className="text-sm text-muted mb-4">Chọn bàn phù hợp với {partySize} khách để giữ chỗ tạm thời.</p>
          {tablesLoading ? (
            <div className="text-sm text-muted py-4">Đang tải danh sách bàn…</div>
          ) : tables.length === 0 ? (
            <div className="text-sm text-muted py-4">Chi nhánh chưa có bàn khả dụng cho ngày giờ này.</div>
          ) : (
            <TablePicker tables={tables} partySize={partySize} selectedTable={selectedTableId} onSelect={onSelectTable} />
          )}
          {holdLoading && <p className="text-sm text-muted mt-4">Đang giữ bàn…</p>}
          {holdError && <p className="text-sm text-primary mt-4">{holdError}</p>}
          {holdInfo && !holdLoading && (
            <div className="flex items-center justify-between flex-wrap gap-3 bg-accent/5 border border-accent/20 rounded-xl px-4 py-3.5 mt-4">
              <span className="text-sm">Bàn đã được giữ tạm trong thời gian hoàn tất đặt chỗ.</span>
              <HoldCountdown until={holdInfo.heldUntil} label="Còn lại" />
            </div>
          )}
        </section>
      )}

      {/* Continue button */}
      {selectedTableId && holdInfo && !holdLoading && (
        <div className="flex justify-end">
          <button
            onClick={onContinue}
            className="px-8 py-3 bg-dark text-white rounded-xl font-semibold hover:bg-dark/80 transition-colors"
          >
            Tiếp tục →
          </button>
        </div>
      )}
    </div>
  );
}
