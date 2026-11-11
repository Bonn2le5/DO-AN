import { useState } from "react";
import { Link } from "react-router-dom";
import { Check, Star, UtensilsCrossed } from "lucide-react";
import { guiDanhGiaBuaAn } from "@/api/reviews.api";
import RatingStars from "@/components/ui/RatingStars";
import { cn, formatDate } from "@/lib/utils";
import type { BuaAnChoDanhGia } from "@/types";

// Nhãn dùng chung cho món, phục vụ và không gian nên tránh từ chỉ dành cho đồ ăn ("Ngon")
const NHAN_SAO = ["", "Rất tệ", "Chưa tốt", "Tạm được", "Tốt", "Tuyệt vời"];

function ChonSao({ value, onChange, label }: { value: number; onChange: (n: number) => void; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-0.5" role="radiogroup" aria-label={label}>
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            role="radio"
            aria-checked={value === n}
            aria-label={`${n} sao`}
            onClick={() => onChange(value === n ? 0 : n)}
            className="p-0.5 rounded focus-visible:outline-2 focus-visible:outline-primary"
          >
            <Star width={22} height={22} className={n <= value ? "fill-accent stroke-accent" : "fill-none stroke-muted"} />
          </button>
        ))}
      </div>
      <span className="text-xs text-muted w-20">{NHAN_SAO[value]}</span>
    </div>
  );
}

type Nhap = Record<string, { diem: number; nhanXet: string }>;

export default function MealReviewCard({ buaAn, onDone }: { buaAn: BuaAnChoDanhGia; onDone: () => void }) {
  const [mon, setMon] = useState<Nhap>({});
  const [phucVu, setPhucVu] = useState(0);
  const [khongGian, setKhongGian] = useState(0);
  const [nhanXetChung, setNhanXetChung] = useState("");
  const [busy, setBusy] = useState(false);
  const [loi, setLoi] = useState("");

  const monDaChon = Object.entries(mon).filter(([, v]) => v.diem > 0);
  const canChung = !buaAn.danhGiaChung;
  const chungDangDo = canChung && (phucVu > 0) !== (khongGian > 0);
  const coChung = canChung && phucVu > 0 && khongGian > 0;
  const coTheGui = !busy && !chungDangDo && (monDaChon.length > 0 || coChung);

  const datMon = (id: string, patch: Partial<{ diem: number; nhanXet: string }>) =>
    setMon((cu) => ({ ...cu, [id]: { ...(cu[id] ?? { diem: 0, nhanXet: "" }), ...patch } }));

  const gui = async () => {
    setBusy(true);
    setLoi("");
    try {
      await guiDanhGiaBuaAn({
        idDonHang: buaAn.id,
        mon: monDaChon.map(([idChiTiet, v]) => ({ idChiTiet, diemDanhGia: v.diem, nhanXet: v.nhanXet.trim() })),
        chung: coChung ? { diemPhucVu: phucVu, diemKhongGian: khongGian, nhanXet: nhanXetChung.trim() } : undefined,
      });
      onDone();
    } catch (err: any) {
      const d = err?.response?.data;
      const msg = d?.mon ?? d?.don_hang ?? d?.diem_phuc_vu ?? d?.non_field_errors ?? d?.detail;
      setLoi(Array.isArray(msg) ? String(msg[0]) : msg ? String(msg) : "Không gửi được đánh giá. Vui lòng thử lại.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <article className="card p-5 md:p-6">
      <header className="flex flex-wrap items-baseline justify-between gap-2 mb-4">
        <h3 className="font-semibold">
          Bữa ăn {buaAn.chiNhanh ? `tại ${buaAn.chiNhanh}` : ""} · {formatDate(buaAn.taoLuc)}
        </h3>
        <span className="text-xs text-muted">Đơn {buaAn.maDonHang}</span>
      </header>

      <ul className="divide-y divide-black/[0.06]">
        {buaAn.mon.map((m) => {
          const nhap = mon[m.idChiTiet];
          return (
            <li key={m.idChiTiet} className="py-3 first:pt-0">
              <div className="flex flex-wrap items-center gap-3">
                <div className="w-12 h-12 rounded-lg bg-black/5 overflow-hidden shrink-0 flex items-center justify-center">
                  {m.duongDanAnh ? (
                    <img src={m.duongDanAnh} alt="" className="w-full h-full object-cover" loading="lazy" />
                  ) : (
                    <UtensilsCrossed width={18} height={18} className="text-muted" />
                  )}
                </div>
                <div className="flex-1 min-w-32">
                  <Link to={`/thuc-don/${m.duongDanMon}`} className="text-sm font-medium hover:text-primary">
                    {m.tenMon}
                  </Link>
                  {m.soLuong > 1 && <span className="text-xs text-muted"> × {m.soLuong}</span>}
                </div>
                {m.danhGia ? (
                  <div className="flex items-center gap-2 text-xs text-muted">
                    <RatingStars rating={m.danhGia.diemDanhGia} size={15} />
                    <Check width={14} height={14} className="text-success" />
                    Đã đánh giá
                  </div>
                ) : (
                  <ChonSao label={`Chấm điểm ${m.tenMon}`} value={nhap?.diem ?? 0} onChange={(n) => datMon(m.idChiTiet, { diem: n })} />
                )}
              </div>
              {!m.danhGia && (nhap?.diem ?? 0) > 0 && (
                <textarea
                  value={nhap?.nhanXet ?? ""}
                  onChange={(e) => datMon(m.idChiTiet, { nhanXet: e.target.value })}
                  placeholder={`Cảm nhận về ${m.tenMon} (không bắt buộc)`}
                  aria-label={`Nhận xét ${m.tenMon}`}
                  rows={2}
                  maxLength={1000}
                  className="mt-3 w-full px-3 py-2 rounded-xl border border-black/15 text-sm outline-none focus:border-primary resize-none"
                />
              )}
            </li>
          );
        })}
      </ul>

      {canChung ? (
        <section className="mt-5 pt-5 border-t border-black/[0.08]">
          <h4 className="text-sm font-semibold mb-3">Cảm nhận chung về bữa ăn</h4>
          <div className="grid sm:grid-cols-2 gap-3 mb-3">
            <div>
              <p className="text-xs text-muted mb-1">Phục vụ</p>
              <ChonSao label="Chấm điểm phục vụ" value={phucVu} onChange={setPhucVu} />
            </div>
            <div>
              <p className="text-xs text-muted mb-1">Không gian</p>
              <ChonSao label="Chấm điểm không gian" value={khongGian} onChange={setKhongGian} />
            </div>
          </div>
          <textarea
            value={nhanXetChung}
            onChange={(e) => setNhanXetChung(e.target.value)}
            placeholder="Góp ý cho nhà hàng (không bắt buộc)"
            aria-label="Nhận xét chung"
            rows={2}
            maxLength={2000}
            className="w-full px-3 py-2 rounded-xl border border-black/15 text-sm outline-none focus:border-primary resize-none"
          />
          {chungDangDo && <p className="text-xs text-primary mt-1">Hãy chấm cả phục vụ và không gian.</p>}
        </section>
      ) : (
        <p className="mt-4 pt-4 border-t border-black/[0.08] text-xs text-muted flex items-center gap-2">
          <Check width={14} height={14} className="text-success" />
          Đã đánh giá chung: phục vụ {buaAn.danhGiaChung!.diemPhucVu}★, không gian {buaAn.danhGiaChung!.diemKhongGian}★
        </p>
      )}

      <footer className="mt-5 flex flex-wrap items-center gap-3">
        <button type="button" onClick={gui} disabled={!coTheGui} className={cn("btn btn-primary", !coTheGui && "opacity-40 cursor-not-allowed")}>
          {busy ? "Đang gửi…" : "Gửi đánh giá"}
        </button>
        <span className="text-xs text-muted">Chỉ cần chấm món bạn muốn, phần còn lại có thể đánh giá sau.</span>
        {loi && <p className="w-full text-sm text-primary">{loi}</p>}
      </footer>
    </article>
  );
}
