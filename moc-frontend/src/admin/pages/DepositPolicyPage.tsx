import { useEffect, useState } from "react";
import { Info } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getDepositPolicy, saveDepositPolicy } from "../api/admin.api";
import { PageHeader, inputCls } from "../components/primitives";
import { useToast } from "../components/toast";
import { useCan } from "../permissions";
import type { DepositPolicyData } from "../types";

const BUCKET = { ">24h": "Huỷ trước giờ hẹn hơn 24 giờ", "6-24h": "Huỷ trước giờ hẹn 6–24 giờ", "<6h": "Huỷ trong vòng 6 giờ", no_show: "Khách không đến" };

export default function DepositPolicyPage() {
  const can = useCan();
  const push = useToast((s) => s.push);
  const { data, loading } = useAsync(() => getDepositPolicy());
  const [form, setForm] = useState<DepositPolicyData | null>(null);
  const [saving, setSaving] = useState(false);
  useEffect(() => { if (data) setForm(data); }, [data]);

  const editable = can("deposit", "update");
  const num = (v: string) => Math.max(0, Number(v) || 0);

  const save = async () => {
    if (!form) return;
    setSaving(true);
    await saveDepositPolicy(form);
    push("Đã lưu chính sách cọc");
    setSaving(false);
  };

  if (loading || !form) return <div className="card h-96 animate-pulse bg-black/5" />;

  return (
    <div className="max-w-3xl">
      <PageHeader title="Chính sách cọc" subtitle="Áp dụng cho đặt bàn kèm gọi món trước. Đặt bàn không gọi món thì không cần cọc." />
      <div className="rounded-2xl bg-secondary/12 border border-secondary/50 p-4 flex gap-3 text-sm mb-6">
        <Info width={18} height={18} className="shrink-0 mt-0.5 text-[#8a4b1d]" />
        <p className="leading-relaxed">Hệ thống <b>không tự động hoàn tiền</b>. Khi khách huỷ, khoản cọc vào hàng chờ; lễ tân/CSKH xác minh, chuyển khoản thủ công và ghi nhận. Tỉ lệ dưới đây chỉ là mức <b>gợi ý</b> hiện sẵn khi nhân viên ghi nhận hoàn cọc.</p>
      </div>

      <div className="space-y-6">
        <section className="card p-6">
          <h2 className="font-display text-lg mb-4">Đặt cọc</h2>
          <div className="grid sm:grid-cols-3 gap-4">
            {([["depositPercentage", "Tỉ lệ cọc (% tiền món)"], ["holdMinutes", "Giữ bàn tạm (phút)"], ["paymentDeadlineMinutes", "Hạn thanh toán (phút)"]] as const).map(([k, label]) => (
              <div key={k}>
                <label htmlFor={k} className="text-[13px] font-semibold text-muted block mb-1.5">{label}</label>
                <input id={k} type="number" min={0} disabled={!editable} value={form[k]} onChange={(e) => setForm({ ...form, [k]: num(e.target.value) })} className={inputCls} />
              </div>
            ))}
          </div>
        </section>

        <section className="card p-6">
          <h2 className="font-display text-lg mb-1">Mức hoàn gợi ý theo thời điểm huỷ</h2>
          <p className="text-sm text-muted mb-4">Tính trên số tiền cọc đã thanh toán.</p>
          <div className="divide-y divide-black/[0.07]">
            {form.rules.map((r, i) => (
              <div key={r.bucket} className="flex items-center justify-between gap-4 py-3">
                <span className="text-sm">{BUCKET[r.bucket]}</span>
                <div className="flex items-center gap-2">
                  <input
                    type="number" min={0} max={100} disabled={!editable} aria-label={BUCKET[r.bucket]} value={r.refundPercentage}
                    onChange={(e) => setForm({ ...form, rules: form.rules.map((x, j) => (j === i ? { ...x, refundPercentage: Math.min(100, num(e.target.value)) } : x)) })}
                    className={`${inputCls} w-24! text-right`}
                  />
                  <span className="text-sm text-muted">%</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="card p-6">
          <h2 className="font-display text-lg mb-4">Thông tin hướng dẫn cho khách</h2>
          <label htmlFor="hotline" className="text-[13px] font-semibold text-muted block mb-1.5">Số liên hệ lễ tân / CSKH</label>
          <input id="hotline" disabled={!editable} value={form.hotline} onChange={(e) => setForm({ ...form, hotline: e.target.value })} className={`${inputCls} sm:w-64 mb-4`} />
          <label htmlFor="guide" className="text-[13px] font-semibold text-muted block mb-1.5">Nội dung hiển thị khi khách đặt cọc và huỷ bàn</label>
          <textarea id="guide" rows={4} disabled={!editable} value={form.guideText} onChange={(e) => setForm({ ...form, guideText: e.target.value })} className={`${inputCls} resize-none`} />
        </section>

        {editable && <div className="flex justify-end"><button className="btn btn-primary" disabled={saving} onClick={save}>{saving ? "Đang lưu..." : "Lưu chính sách"}</button></div>}
      </div>
    </div>
  );
}
