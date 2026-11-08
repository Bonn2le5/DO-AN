import { useEffect, useState } from "react";
import { MapPin, Phone, Clock, Minus, Plus, Search } from "lucide-react";
import { formatLongDate } from "./ReservationTicket";
import { cn, localDateInputValue } from "@/lib/utils";
import type { Branch } from "@/types";
import { layDanhSachChiNhanh, layKhungGioTrong } from "@/api/reservations.api";

interface BranchTimeStepProps {
  selectedBranchId: string;
  onBranchChange: (id: string) => void;
  date: string;
  onDateChange: (v: string) => void;
  partySize: number;
  onPartySizeChange: (v: number) => void;
  selectedTime: string;
  onTimeSelect: (time: string) => void;
  onContinue: (branchId: string, branchName: string, time: string) => void;
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
  onContinue,
}: BranchTimeStepProps) {
  const [branches, setBranches] = useState<Branch[]>([]);
  const [slots, setSlots] = useState<{ khungGio: string; conTrong: boolean; soChoConLai: number }[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [searched, setSearched] = useState(false);
  const [partySizeError, setPartySizeError] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    layDanhSachChiNhanh().then(setBranches);
  }, []);

  const selectedBranch = branches.find((b) => b.id === selectedBranchId) ?? null;
  const visibleSlots = date === localDateInputValue()
    ? slots.filter((slot) => {
        const [hour, minute] = slot.khungGio.split(":").map(Number);
        const now = new Date();
        return hour * 60 + minute > now.getHours() * 60 + now.getMinutes();
      })
    : slots;

  useEffect(() => {
    if (!selectedTime || !loaded) return;
    const now = new Date();
    const isPastToday = date === localDateInputValue() && (() => {
      const [hour, minute] = selectedTime.split(":").map(Number);
      return hour * 60 + minute <= now.getHours() * 60 + now.getMinutes();
    })();
    if (isPastToday || !slots.some((slot) => slot.khungGio === selectedTime && slot.conTrong)) {
      onTimeSelect("");
    }
  }, [date, slots, selectedTime, onTimeSelect, loaded]);

  const handleSearch = async (keepTime = false) => {
    if (!selectedBranchId || !date) return;
    setLoadingSlots(true);
    setSearched(true);
    setLoaded(false);
    if (!keepTime) onTimeSelect("");
    if (!Number.isInteger(partySize) || partySize < 1 || partySize > 12) {
      setPartySizeError(true);
      setSlots([]);
      setLoadingSlots(false);
      return;
    }
    setPartySizeError(false);
    try {
      const result = await layKhungGioTrong({
        chiNhanhId: selectedBranchId,
        ngay: date,
        soKhach: partySize,
      });
      setSlots(result);
      setLoaded(true);
    } finally {
      setLoadingSlots(false);
    }
  };

  // Quay lại từ bước sau: tự tải lại khung giờ và giữ giờ đã chọn nếu còn trống.
  useEffect(() => {
    if (selectedBranchId && date && selectedTime) void handleSearch(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const resetSearch = () => {
    onTimeSelect("");
    setSearched(false);
    setLoaded(false);
  };

  const setParty = (value: number) => {
    onPartySizeChange(value);
    resetSearch();
    setPartySizeError(false);
  };

  const canContinue = Boolean(selectedTime) && visibleSlots.some((slot) => slot.khungGio === selectedTime && slot.conTrong);
  const continueToFood = () => onContinue(selectedBranchId, selectedBranch?.name ?? "", selectedTime);

  return (
    <div className={cn("space-y-6", canContinue && "pb-24 md:pb-0")}>
      <section className="bg-white rounded-[20px] border border-black/[0.07] p-5 sm:p-6">
        <div className="grid sm:grid-cols-2 lg:grid-cols-[1.3fr_1fr_1fr_auto] gap-4 lg:items-end">
          <div className="sm:col-span-2 lg:col-span-1">
            <label htmlFor="reservation-branch" className="text-sm font-semibold block mb-1.5">Chi nhánh</label>
            <select
              id="reservation-branch"
              value={selectedBranchId}
              onChange={(e) => {
                onBranchChange(e.target.value);
                resetSearch();
              }}
              className="reservation-field"
            >
              <option value="">Chọn chi nhánh</option>
              {branches.map((b) => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="reservation-date" className="text-sm font-semibold block mb-1.5">Ngày</label>
            <input
              id="reservation-date"
              type="date"
              value={date}
              min={localDateInputValue()}
              onChange={(e) => {
                onDateChange(e.target.value);
                resetSearch();
              }}
              className="reservation-field"
            />
          </div>

          <div>
            <label htmlFor="reservation-party" className="text-sm font-semibold block mb-1.5">Số khách</label>
            <div className="flex items-center rounded-xl border border-black/15 bg-white focus-within:border-primary">
              <button type="button" aria-label="Bớt một khách" disabled={partySize <= 1} onClick={() => setParty(Math.max(1, partySize - 1))} className="w-12 h-12 flex items-center justify-center text-muted hover:text-primary disabled:opacity-30">
                <Minus size={16} />
              </button>
              <input
                id="reservation-party"
                type="number"
                inputMode="numeric"
                min={1}
                max={12}
                step={1}
                value={partySize || ""}
                onChange={(e) => setParty(e.target.value === "" ? 0 : Number(e.target.value))}
                className="flex-1 min-w-0 text-center text-[15px] font-semibold outline-none bg-transparent [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none"
              />
              <button type="button" aria-label="Thêm một khách" disabled={partySize >= 12} onClick={() => setParty(Math.min(12, partySize + 1))} className="w-12 h-12 flex items-center justify-center text-muted hover:text-primary disabled:opacity-30">
                <Plus size={16} />
              </button>
            </div>
          </div>

          <button
            type="button"
            onClick={() => handleSearch()}
            disabled={!selectedBranchId || !date || loadingSlots}
            className="btn btn-primary sm:col-span-2 lg:col-span-1 h-[50px] py-0! disabled:opacity-50 disabled:shadow-none disabled:hover:translate-y-0"
          >
            <Search size={18} />
            {loadingSlots ? "Đang tìm…" : "Xem giờ trống"}
          </button>
        </div>
        <p className="text-xs text-muted mt-3">Đặt online tối đa 12 khách. Nhóm đông hơn, vui lòng gọi chi nhánh.</p>
      </section>

      {searched && partySizeError && (
        <p className="rounded-xl border border-primary/20 bg-primary/5 px-4 py-3 text-sm text-primary" role="alert">
          Số khách phải từ 1 đến 12. Sửa lại số khách rồi bấm Xem giờ trống.
        </p>
      )}

      {searched && !partySizeError && selectedBranch && (
        <section className="bg-white rounded-[20px] border border-black/[0.07] p-5 sm:p-6 grid md:grid-cols-[240px_1fr] gap-6 md:gap-8">
          <div>
            <h3 className="font-display text-lg leading-snug">{selectedBranch.name}</h3>
            <div className="mt-3 space-y-2 text-sm text-muted">
              <div className="flex gap-2"><MapPin size={15} className="shrink-0 mt-0.5" /><span>{selectedBranch.address}</span></div>
              {selectedBranch.phone && <div className="flex gap-2"><Phone size={15} className="shrink-0 mt-0.5" /><a href={`tel:${selectedBranch.phone}`} className="hover:text-primary">{selectedBranch.phone}</a></div>}
              {selectedBranch.openHours && <div className="flex gap-2"><Clock size={15} className="shrink-0 mt-0.5" /><span>{selectedBranch.openHours}</span></div>}
            </div>
          </div>

          <div>
            <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 mb-3">
              <h3 className="font-semibold">Giờ trống ngày {formatLongDate(date)}</h3>
              <span className="text-xs text-muted">{partySize} khách</span>
            </div>

            {loadingSlots ? (
              <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
                {Array.from({ length: 12 }).map((_, i) => <div key={i} className="h-14 rounded-xl bg-black/5 animate-pulse" />)}
              </div>
            ) : slots.length === 0 ? (
              <p className="text-sm text-muted py-4">Chưa tải được khung giờ. Bấm Xem giờ trống để thử lại.</p>
            ) : visibleSlots.length === 0 ? (
              <p className="text-sm text-muted py-4">Hôm nay đã hết khung giờ nhận đặt bàn. Chọn ngày khác để xem giờ trống.</p>
            ) : (
              <div className="grid grid-cols-4 sm:grid-cols-6 gap-2" role="radiogroup" aria-label="Khung giờ">
                {visibleSlots.map((slot) => {
                  const selected = slot.conTrong && selectedTime === slot.khungGio;
                  return (
                    <button
                      key={slot.khungGio}
                      type="button"
                      role="radio"
                      aria-checked={selected}
                      disabled={!slot.conTrong}
                      onClick={() => onTimeSelect(slot.khungGio)}
                      className={cn(
                        "h-14 rounded-xl border flex flex-col items-center justify-center transition-colors",
                        !slot.conTrong && "border-transparent bg-black/[0.04] text-muted/60 cursor-not-allowed",
                        slot.conTrong && !selected && "border-black/12 bg-white hover:border-primary hover:text-primary",
                        selected && "border-primary bg-primary text-white",
                      )}
                    >
                      <span className={cn("text-[15px] font-semibold tabular-nums", !slot.conTrong && "line-through")}>{slot.khungGio}</span>
                      <span className={cn("text-[11px]", selected ? "text-white/80" : "text-muted")}>
                        {slot.conTrong ? `còn ${slot.soChoConLai} chỗ` : "hết chỗ"}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </section>
      )}

      {canContinue && (
        <div className="reservation-sticky-bar fixed md:static inset-x-0 bottom-0 z-30 border-t md:border-0 border-black/10 bg-bg/95 md:bg-transparent backdrop-blur md:backdrop-blur-none px-4 py-3 md:p-0">
          <div className="max-w-xl md:max-w-none mx-auto flex items-center justify-between gap-4">
            <div className="min-w-0">
              <div className="font-display text-lg leading-tight tabular-nums">{selectedTime} · {partySize} khách</div>
              <div className="text-xs sm:text-sm text-muted truncate">{formatLongDate(date)}</div>
            </div>
            <button type="button" onClick={continueToFood} className="btn btn-primary px-5! sm:px-7! py-3! shrink-0">
              Tiếp tục
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
