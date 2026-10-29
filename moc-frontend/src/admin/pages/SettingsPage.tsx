import { useState } from "react";
import { PageHeader, inputCls } from "../components/primitives";
import { useToast } from "../components/toast";
import { changePassword, getRestaurantSettings, saveRestaurantSettings } from "../api/admin.api";
import { useEffect } from "react";

export default function SettingsPage() {
  const push = useToast((s) => s.push);
  const [info, setInfo] = useState({ name: "MỘC Kitchen", email: "hello@moc-kitchen.vn", weekday: "10:00 – 22:00", weekend: "09:00 – 23:00" });
  const [pw, setPw] = useState({ current: "", next: "", confirm: "" });
  const [error, setError] = useState("");
  useEffect(() => { void getRestaurantSettings().then(setInfo).catch(() => undefined); }, []);

  const saveInfo = async () => {
    try { const saved = await saveRestaurantSettings(info); setInfo(saved); push("Đã lưu thông tin"); }
    catch (e) { push(e instanceof Error ? e.message : "Không lưu được thông tin", "err"); }
  };

  const submitPassword = async () => {
    if (pw.next.length < 8) return setError("Mật khẩu mới tối thiểu 8 ký tự");
    if (pw.next !== pw.confirm) return setError("Mật khẩu xác nhận không khớp");
    try { await changePassword(pw.current, pw.next); setError(""); setPw({ current: "", next: "", confirm: "" }); push("Đã đổi mật khẩu"); }
    catch (e) { setError(e instanceof Error ? e.message : "Không đổi được mật khẩu"); }
  };

  const field = (label: string, key: keyof typeof info) => (
    <div key={key}>
      <label htmlFor={key} className="text-[13px] font-semibold text-muted block mb-1.5">{label}</label>
      <input id={key} value={info[key]} onChange={(e) => setInfo({ ...info, [key]: e.target.value })} className={inputCls} />
    </div>
  );

  return (
    <div className="max-w-2xl space-y-6">
      <PageHeader title="Cài đặt" />
      <section className="card p-6">
        <h2 className="font-display text-lg mb-4">Thông tin nhà hàng</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          {field("Tên nhà hàng", "name")}{field("Email liên hệ", "email")}{field("Giờ mở cửa (T2–T6)", "weekday")}{field("Giờ mở cửa (T7–CN)", "weekend")}
        </div>
        <div className="flex justify-end mt-5"><button className="btn btn-primary py-2.5! px-5! text-sm!" onClick={saveInfo}>Lưu thông tin</button></div>
      </section>
      <section className="card p-6">
        <h2 className="font-display text-lg mb-4">Đổi mật khẩu</h2>
        <div className="space-y-4 sm:max-w-sm">
          {([["current", "Mật khẩu hiện tại"], ["next", "Mật khẩu mới"], ["confirm", "Nhập lại mật khẩu mới"]] as const).map(([k, label]) => (
            <div key={k}>
              <label htmlFor={`pw-${k}`} className="text-[13px] font-semibold text-muted block mb-1.5">{label}</label>
              <input id={`pw-${k}`} type="password" value={pw[k]} onChange={(e) => setPw({ ...pw, [k]: e.target.value })} className={inputCls} />
            </div>
          ))}
          {error && <p className="text-xs text-primary">{error}</p>}
          <button className="btn btn-outline py-2.5! px-5! text-sm!" onClick={submitPassword}>Đổi mật khẩu</button>
        </div>
      </section>
    </div>
  );
}
