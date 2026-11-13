import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { Check, Loader2, RefreshCw, RotateCcw, SendHorizontal, Sparkles, UtensilsCrossed, X } from "lucide-react";
import { hoiTroLyGoiMon, ghiSuKienGoiY } from "@/api/recommendations.api";
import PlaceholderMedia from "@/components/ui/PlaceholderMedia";
import { cn, formatCurrency } from "@/lib/utils";
import type { MonAnDatBan, NhomMonThucDon, ThucDonTroLy } from "@/types";

// Mỗi nút có JSON ý định cố định ở backend (GOI_Y_NHANH trong recommendations/tro_ly.py), không gọi AI.
// "cau" là câu gốc để các lần "Điều chỉnh" sau đó cho AI đọc tiếp.
const GOI_Y_NHANH = [
  { khoa: "lau_nuong", nhan: "Lẩu nướng", cau: (n: number) => `Lẩu nướng cho ${n} người` },
  { khoa: "gia_dinh", nhan: "Gia đình", cau: (n: number) => `Bữa gia đình ${n} người, không cay` },
  { khoa: "tiet_kiem", nhan: "Tiết kiệm", cau: (n: number) => `${n} người, tiết kiệm` },
  { khoa: "nhieu_thit", nhan: "Nhiều thịt", cau: (n: number) => `${n} người, nhiều thịt` },
  { khoa: "hai_san", nhan: "Hải sản", cau: (n: number) => `${n} người, thích hải sản` },
  { khoa: "lai_rai", nhan: "Lai rai", cau: (n: number) => `${n} người, nhâm nhi lai rai` },
];

/**
 * Trợ lý gọi món AI (bước gọi món khi đặt bàn).
 * Khách gõ một câu ("lẩu nướng lai rai, cay một chút, 4 người 1 triệu") → AI đọc thành JSON ý định
 * (nhóm món, dịp, vị, sở thích, điều cần tránh, số người, ngân sách) → backend truy vấn database chọn món
 * theo số người, ràng buộc và ngân sách. "Điều chỉnh" gửi thêm câu mới.
 * Thực đơn chia tab theo nhóm món; khách bỏ tick món không thích hoặc bấm "Đổi món" (lấy món dự phòng
 * backend trả kèm), rồi mới thêm các món còn tick vào "Món đã chọn".
 */
const NUT =
  "h-9 flex-auto sm:flex-none whitespace-nowrap rounded-full px-4 text-sm font-medium inline-flex items-center justify-center gap-1.5 transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary";

export default function TroLyGoiMon({
  partySize,
  onAddMany,
}: {
  partySize: number;
  onAddMany: (items: MonAnDatBan[]) => void;
}) {
  const [cau, setCau] = useState("");
  const [yeuCauGoc, setYeuCauGoc] = useState("");
  const [dieuChinh, setDieuChinh] = useState<string[]>([]);
  const [dangDieuChinh, setDangDieuChinh] = useState(false);
  const [thucDon, setThucDon] = useState<ThucDonTroLy | null>(null);
  // Bản đang hiển thị của thucDon.nhomMon, đã áp các lần "Đổi món".
  const [nhom, setNhom] = useState<NhomMonThucDon[]>([]);
  const [tab, setTab] = useState("");
  const [boTick, setBoTick] = useState<string[]>([]);
  // Món đã bị đổi đi, hoặc bị bỏ tick ở các lần điều chỉnh trước: gửi kèm để backend không đưa lại.
  const [monBiLoai, setMonBiLoai] = useState<string[]>([]);
  const [dangHoi, setDangHoi] = useState(false);
  const [loi, setLoi] = useState("");
  const [daThem, setDaThem] = useState(false);
  // Những món trợ lý đã đưa vào "Món đã chọn": thêm thực đơn mới thì thay phần này (không cộng dồn),
  // "Bỏ các món đã thêm" thì gỡ đúng phần này, món khách tự chọn giữ nguyên.
  const [monDaThem, setMonDaThem] = useState<MonAnDatBan[]>([]);
  const am = (ds: MonAnDatBan[]) => ds.map((m) => ({ ...m, soLuong: -m.soLuong }));
  const oNhap = useRef<HTMLInputElement>(null);

  const hoi = async (goc: string, cacDieuChinh: string[], goiYNhanh?: string, loaiBo: string[] = []) => {
    setDangHoi(true);
    setLoi("");
    setDaThem(false);
    try {
      const kq = await hoiTroLyGoiMon(goc, cacDieuChinh, partySize, goiYNhanh, loaiBo);
      setYeuCauGoc(goc);
      setDieuChinh(cacDieuChinh);
      setThucDon(kq);
      setNhom(kq.nhomMon);
      setTab(kq.nhomMon[0]?.khoa ?? "");
      setBoTick([]);
      setMonBiLoai(loaiBo);
      setDangDieuChinh(false);
      setCau("");
    } catch (e) {
      // 400 = yêu cầu không hợp lệ (vd. quá 10 lần điều chỉnh), thử lại y nguyên cũng không được
      const ma = (e as { response?: { status?: number } })?.response?.status;
      if (ma === 400) {
        setLoi(
          cacDieuChinh.length >= 10
            ? "Bạn đã điều chỉnh thực đơn này nhiều lần rồi. Bấm “Hỏi lại” để bắt đầu thực đơn mới nhé."
            : "Mộc chưa đọc được yêu cầu này. Bạn thử viết ngắn gọn hơn nhé.",
        );
      } else if (ma === 401) {
        setLoi("Bạn đăng nhập để hỏi trợ lý AI nhé. Các nút gợi ý nhanh vẫn dùng được.");
      } else if (ma === 429) {
        setLoi("Bạn hỏi hơi nhanh, chờ khoảng một phút rồi thử lại nhé.");
      } else {
        setLoi("Trợ lý AI đang bận, bạn thử lại sau ít phút nhé.");
      }
    } finally {
      setDangHoi(false);
    }
  };

  const gui = (e?: FormEvent) => {
    e?.preventDefault();
    const text = cau.trim();
    if (!text || dangHoi) return;
    if (dangDieuChinh && yeuCauGoc) hoi(yeuCauGoc, [...dieuChinh, text], undefined, [...new Set([...monBiLoai, ...boTick])]);
    else hoi(text, []);
  };

  // tatCaMon: thực đơn gốc AI trả (để ghi sự kiện hiển thị); monChon: các món còn tick sau khi khách sửa.
  const tatCaMon = thucDon?.nhomMon.flatMap((g) => g.mon) ?? [];
  const conTick = (id: string) => !boTick.includes(id);
  const monChon = nhom.flatMap((g) => g.mon).filter((m) => conTick(m.monAn.id));
  const tongTien = monChon.reduce((t, m) => t + m.thanhTien, 0);
  const vuotNganSach = Boolean(thucDon?.nganSach && tongTien > thucDon.nganSach);
  const nhomDangMo = nhom.find((g) => g.khoa === tab) ?? nhom[0];

  const doiTick = (id: string) => {
    setBoTick((cur) => (cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id]));
    setDaThem(false);
  };

  const doiMon = (khoa: string, id: string) => {
    setNhom((cur) =>
      cur.map((g) => {
        if (g.khoa !== khoa || !g.duPhong.length) return g;
        const [moi, ...conLai] = g.duPhong;
        return { ...g, mon: g.mon.map((m) => (m.monAn.id === id ? moi : m)), duPhong: conLai };
      }),
    );
    setMonBiLoai((cur) => [...cur, id]);
    setDaThem(false);
  };

  useEffect(() => {
    if (tatCaMon.length) {
      ghiSuKienGoiY(
        "hien_thi",
        "tro_ly",
        tatCaMon.map((m) => ({ monAn: m.monAn, diemTuongDong: 0, lyDoGoiY: "", phienBanMoHinh: thucDon?.phienBanMoHinh })),
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [thucDon]);

  const themToanBo = () => {
    if (!monChon.length) return;
    const moi = monChon.map((m) => ({ monAn: m.monAn, soLuong: m.soLuong }));
    onAddMany([...am(monDaThem), ...moi]);
    setMonDaThem(moi);
    ghiSuKienGoiY(
      "nhap",
      "tro_ly",
      monChon.map((m) => ({ monAn: m.monAn, diemTuongDong: 0, lyDoGoiY: "", phienBanMoHinh: thucDon?.phienBanMoHinh })),
    );
    setDaThem(true);
  };

  const boMonDaThem = () => {
    onAddMany(am(monDaThem));
    setMonDaThem([]);
    setDaThem(false);
  };

  const batDauDieuChinh = () => {
    setDangDieuChinh(true);
    setCau("");
    setTimeout(() => oNhap.current?.focus(), 0);
  };

  const lamLai = () => {
    setThucDon(null);
    setNhom([]);
    setBoTick([]);
    setMonBiLoai([]);
    setYeuCauGoc("");
    setDieuChinh([]);
    setDangDieuChinh(false);
    setDaThem(false);
    setCau("");
  };

  const pt = thucDon?.phanTich;

  return (
    <section aria-label="Trợ lý gọi món AI" className="font-['Be_Vietnam_Pro',ui-sans-serif,system-ui,sans-serif] [--font-display:'Be_Vietnam_Pro',ui-sans-serif,system-ui,sans-serif] mb-6 rounded-2xl border border-black/[0.08] bg-white shadow-soft overflow-hidden">
      <div className="px-5 pt-5 pb-4 text-center">
        <span className="inline-block rounded-full bg-primary/10 text-primary text-xs font-semibold px-2.5 py-0.5">AI Mộc</span>
        <h3 className="text-xl font-semibold mt-2">Hôm nay bạn muốn ăn gì?</h3>
        <p className="text-sm text-muted mt-0.5">Mộc gợi ý một thực đơn vừa khẩu vị và ngân sách của bạn.</p>
      </div>

      <div className="px-5 pb-5">
        <form onSubmit={gui} className="rounded-xl border border-black/12 focus-within:border-primary/60 transition-colors p-3">
          <div className="flex items-center gap-1.5 text-sm font-semibold mb-1">
            <Sparkles size={16} className="text-primary" aria-hidden="true" />
            {dangDieuChinh ? "Điều chỉnh thực đơn" : "Trợ lý gọi món AI"}
          </div>
          {dangDieuChinh && (
            <p className="text-[13px] text-muted mb-2">Ví dụ: bớt cay, thêm hải sản, đổi thành 6 người, dưới 800k.</p>
          )}
          <div className="flex items-center gap-2">
            <input
              ref={oNhap}
              value={cau}
              onChange={(e) => setCau(e.target.value)}
              maxLength={300}
              placeholder={dangDieuChinh ? "Bạn muốn đổi gì?" : "Tôi muốn ăn lẩu nướng…"}
              aria-label={dangDieuChinh ? "Câu điều chỉnh thực đơn" : "Bạn muốn ăn gì"}
              className="flex-1 min-w-0 bg-transparent outline-none text-[15px] py-2"
            />
            {dangDieuChinh && (
              <button type="button" onClick={() => setDangDieuChinh(false)} aria-label="Huỷ điều chỉnh"
                className="w-10 h-10 rounded-xl text-muted hover:bg-black/5 flex items-center justify-center">
                <X size={18} />
              </button>
            )}
            <button type="submit" disabled={!cau.trim() || dangHoi} aria-label="Gửi yêu cầu"
              className="w-10 h-10 shrink-0 rounded-xl bg-primary text-white flex items-center justify-center disabled:opacity-40 hover:brightness-110 transition">
              {dangHoi ? <Loader2 size={18} className="animate-spin" /> : <SendHorizontal size={18} />}
            </button>
          </div>
          {/* Báo trước khi gửi: câu khách gõ đi tới dịch vụ AI ở nước ngoài, có thể chứa thông tin dị ứng (dữ liệu sức khỏe).
              Điều 9 Luật 91/2025; khoản 4 Điều 6 NĐ 356/2025; checklist 07 mục B. Nút gợi ý nhanh không gọi AI. */}
          <p className="text-xs text-muted leading-relaxed mt-1.5">
            Câu bạn gõ được gửi tới dịch vụ AI để hiểu khẩu vị, không kèm tên hay số điện thoại. Đừng nhập thông tin cá nhân.
            Thông tin dị ứng chỉ dùng để lọc món.{" "}
            <Link to="/chinh-sach-bao-mat#tro-ly-ai" target="_blank" className="underline underline-offset-2 hover:text-primary">Tìm hiểu thêm</Link>
          </p>
        </form>

        {!thucDon && monDaThem.length > 0 && (
          <p className="mt-3 text-sm text-muted">
            Món đã chọn đang có {monDaThem.length} món từ thực đơn trước.{" "}
            <button type="button" onClick={boMonDaThem} className="underline underline-offset-2 hover:text-primary">
              Bỏ các món đó
            </button>
          </p>
        )}

        {!thucDon && (
          <div className="mt-4">
            <div className="text-sm font-medium mb-2">Gợi ý nhanh</div>
            <div className="flex flex-wrap gap-2">
              {GOI_Y_NHANH.map((g) => (
                <button key={g.khoa} type="button" disabled={dangHoi} onClick={() => hoi(g.cau(partySize), [], g.khoa)}
                  className="rounded-full bg-black/[0.05] hover:bg-primary/10 hover:text-primary px-3 py-1.5 text-sm transition-colors disabled:opacity-50">
                  {g.nhan}
                </button>
              ))}
            </div>
          </div>
        )}

        {dangHoi && (
          <p className="mt-3 text-sm text-muted inline-flex items-center gap-1.5" aria-live="polite">
            <Loader2 size={14} className="animate-spin" /> AI Mộc đang lên thực đơn cho bạn…
          </p>
        )}

        {loi && <p role="alert" className="mt-3 text-sm text-red-600">{loi}</p>}

        {thucDon && (
          <div className="mt-5 pt-4 border-t border-black/8" aria-live="polite">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h4 className="font-semibold">Thực đơn AI đề xuất</h4>
                <p className="text-xs text-muted mt-0.5">Chỉ để tham khảo. Nếu có dị ứng, vui lòng báo nhân viên khi đến.</p>
                <p className="text-[13px] text-muted mt-0.5">
                  {pt!.soNguoi} khách
                  {pt!.nganSach ? ` · ngân sách ${formatCurrency(pt!.nganSach)}` : ""}
                  {pt!.khauVi.length ? ` · ${pt!.khauVi.join(", ")}` : ""}
                  {pt!.tranh.length ? ` · tránh ${pt!.tranh.join(", ")}` : ""}
                </p>
                {thucDon.loiNhan && <p className="text-sm mt-2 whitespace-pre-line">{thucDon.loiNhan}</p>}
                {dieuChinh.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {dieuChinh.map((d, i) => (
                      <span key={i} className="text-xs rounded-full bg-accent/15 px-2 py-0.5">{d}</span>
                    ))}
                  </div>
                )}
              </div>
              <button type="button" onClick={lamLai} className="text-xs text-muted hover:text-primary inline-flex items-center gap-1 shrink-0">
                <RotateCcw size={13} /> Hỏi lại
              </button>
            </div>

            {nhom.length === 0 ? (
              <p className="text-sm text-muted mt-4">Chưa tìm được món phù hợp. Thử nói khác đi, ví dụ “lẩu cho 4 người”.</p>
            ) : (
              <div className="mt-3">
                <div role="tablist" aria-label="Nhóm món trong thực đơn"
                  className="flex gap-1.5 overflow-x-auto pb-2 [scrollbar-width:none]">
                  {nhom.map((g) => {
                    const dangMo = g.khoa === nhomDangMo.khoa;
                    return (
                      <button key={g.khoa} type="button" role="tab" aria-selected={dangMo} onClick={() => setTab(g.khoa)}
                        className={cn(
                          "shrink-0 whitespace-nowrap rounded-full px-3 py-1.5 text-sm font-medium inline-flex items-center gap-1.5 transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary",
                          dangMo ? "bg-primary text-white" : "bg-black/[0.05] hover:bg-primary/10 hover:text-primary",
                        )}>
                        {g.ten}
                        <span className={cn("text-xs rounded-full px-1.5 tabular-nums", dangMo ? "bg-white/20" : "bg-black/[0.07]")}>
                          {g.mon.filter((m) => conTick(m.monAn.id)).length}
                        </span>
                      </button>
                    );
                  })}
                </div>
                <ul role="tabpanel" aria-label={nhomDangMo.ten} className="mt-1 divide-y divide-black/[0.06]">
                  {nhomDangMo.mon.map((m) => {
                    const chon = conTick(m.monAn.id);
                    return (
                      <li key={m.monAn.id} className="flex items-center gap-3 text-sm py-2">
                        <label className="flex items-center gap-3 min-w-0 flex-1 cursor-pointer">
                          <input type="checkbox" checked={chon} onChange={() => doiTick(m.monAn.id)}
                            aria-label={`Chọn ${m.monAn.tenMon}`} className="w-4 h-4 shrink-0 accent-primary" />
                          {m.monAn.duongDanAnh ? (
                            <img src={m.monAn.duongDanAnh} alt="" loading="lazy"
                              className={cn("w-14 h-14 rounded-lg object-cover bg-black/5 shrink-0", !chon && "opacity-40")} />
                          ) : (
                            <PlaceholderMedia tone={m.monAn.phongCachHienThi} icon={UtensilsCrossed}
                              className={cn("w-14 h-14 rounded-lg shrink-0", !chon && "opacity-40")} iconClassName="w-5 h-5" />
                          )}
                          <span className={cn("min-w-0 leading-snug", !chon && "line-through text-muted")}>{m.monAn.tenMon}</span>
                        </label>
                        <span className={cn("tabular-nums shrink-0", chon ? "text-muted" : "text-muted/60 line-through")}>
                          {formatCurrency(m.thanhTien)}
                        </span>
                        {nhomDangMo.duPhong.length > 0 && (
                          <button type="button" onClick={() => doiMon(nhomDangMo.khoa, m.monAn.id)}
                            aria-label={`Đổi ${m.monAn.tenMon} sang món khác`}
                            className="shrink-0 inline-flex items-center gap-1 rounded-full border border-black/12 px-2.5 py-1 text-xs text-muted hover:border-primary/50 hover:text-primary transition-colors">
                            <RefreshCw size={12} aria-hidden="true" /> Đổi món
                          </button>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {thucDon.ghiChu.length > 0 && (
              <ul className="text-xs text-muted space-y-0.5 mt-1">
                {thucDon.ghiChu.map((g) => <li key={g}>{g}</li>)}
              </ul>
            )}

            {nhom.length > 0 && (
              <>
                <div className="flex items-center justify-between mt-3 pt-3 border-t border-black/8">
                  <span className="font-semibold">Tổng {monChon.length} món đã chọn</span>
                  <span className={cn("font-semibold tabular-nums", vuotNganSach ? "text-red-600" : "text-primary")}>
                    {formatCurrency(tongTien)}
                  </span>
                </div>
                {daThem && (
                  <p className="mt-3 text-sm text-muted inline-flex items-center gap-1.5" aria-live="polite">
                    <Check size={15} className="text-primary" /> Đã thêm {monDaThem.length} món vào Món đã chọn
                  </p>
                )}
                <div className="flex flex-wrap justify-end gap-2 mt-3">
                  <button type="button" onClick={batDauDieuChinh} className={cn(NUT, "border border-primary/40 text-primary hover:bg-primary/5")}>
                    Điều chỉnh thực đơn với AI
                  </button>
                  {daThem ? (
                    <button type="button" onClick={boMonDaThem} className={cn(NUT, "border border-black/15 text-text hover:bg-black/[0.04]")}>
                      Bỏ các món đã thêm
                    </button>
                  ) : (
                    <button type="button" onClick={themToanBo} disabled={!monChon.length}
                      className={cn(NUT, "bg-primary text-white hover:bg-primary-dark disabled:opacity-40")}>
                      {monDaThem.length ? "Thay thực đơn đã thêm" : `Thêm ${monChon.length} món đã chọn`}
                    </button>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
