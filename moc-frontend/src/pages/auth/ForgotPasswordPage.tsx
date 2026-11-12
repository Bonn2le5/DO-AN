import { useState } from "react";
import { Link } from "react-router-dom";
import { apiErrorMessage, requestPasswordReset, resetPassword } from "@/api/auth.api";

const INPUT = "w-full px-4 py-3.5 rounded-xl border border-black/15 text-sm outline-none focus:border-primary";

export default function ForgotPasswordPage() {
  const [account, setAccount] = useState("");
  const [maskedEmail, setMaskedEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  const run = async (fn: () => Promise<void>, fallback: string) => {
    setBusy(true); setError(""); setInfo("");
    try { await fn(); } catch (e) { setError(apiErrorMessage(e, fallback)); } finally { setBusy(false); }
  };

  const sendCode = (e?: React.FormEvent) => {
    e?.preventDefault();
    return run(async () => {
      setMaskedEmail(await requestPasswordReset(account.trim()));
      if (maskedEmail) setInfo("Đã gửi lại mã.");
    }, "Không gửi được mã, vui lòng thử lại.");
  };

  const submitReset = (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 6) return setError("Mật khẩu tối thiểu 6 ký tự.");
    if (password !== confirm) return setError("Mật khẩu nhập lại không khớp.");
    return run(async () => { await resetPassword(account.trim(), code, password); setDone(true); }, "Đặt lại mật khẩu thất bại.");
  };

  if (done) {
    return (
      <div className="max-w-md mx-auto px-5 py-20 text-center">
        <div className="font-display text-3xl mb-3">Đã đặt lại mật khẩu</div>
        <p className="text-muted text-sm mb-8">Mọi thiết bị đã bị đăng xuất. Hãy đăng nhập bằng mật khẩu mới.</p>
        <Link to="/dang-nhap" className="btn btn-primary w-full py-3.5!">Đăng nhập</Link>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto px-5 py-20">
      {!maskedEmail ? (
        <form key="find" onSubmit={sendCode} className="space-y-4">
          <div className="mb-5">
            <div className="font-display text-3xl mb-2">Tìm tài khoản của bạn</div>
            <p className="text-muted text-sm">Hãy nhập số di động hoặc email của bạn.</p>
          </div>
          <input value={account} onChange={(e) => setAccount(e.target.value)} placeholder="Số di động hoặc email"
            aria-label="Số di động hoặc email" autoComplete="username" className={INPUT} />
          {error && <p className="text-sm text-primary">{error}</p>}
          <button type="submit" disabled={busy || !account.trim()} className="btn btn-primary w-full py-3.5!">
            {busy ? "Đang tìm..." : "Tiếp tục"}
          </button>
        </form>
      ) : (
        <form key="reset" onSubmit={submitReset} className="space-y-4">
          <div className="mb-5">
            <div className="font-display text-3xl mb-2">Đặt lại mật khẩu</div>
            <p className="text-muted text-sm">
              Đã gửi mã 6 số tới <strong className="text-dark">{maskedEmail}</strong>. Mã có hiệu lực 15 phút.
            </p>
          </div>
          <input value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} placeholder="Mã xác thực"
            aria-label="Mã xác thực" inputMode="numeric" autoComplete="one-time-code" maxLength={6} className={INPUT} />
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Mật khẩu mới"
            aria-label="Mật khẩu mới" autoComplete="new-password" className={INPUT} />
          <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="Nhập lại mật khẩu mới"
            aria-label="Nhập lại mật khẩu mới" autoComplete="new-password" className={INPUT} />
          {error && <p className="text-sm text-primary">{error}</p>}
          {info && !error && <p className="text-sm text-emerald-700">{info}</p>}
          <button type="submit" disabled={busy || code.length !== 6} className="btn btn-primary w-full py-3.5!">
            {busy ? "Đang lưu..." : "Đặt lại mật khẩu"}
          </button>
          <div className="flex justify-between text-sm">
            <button type="button" onClick={() => { setMaskedEmail(""); setCode(""); setError(""); }} className="text-muted">
              Nhập tài khoản khác
            </button>
            <button type="button" onClick={() => sendCode()} disabled={busy} className="text-primary font-semibold">
              Gửi lại mã
            </button>
          </div>
        </form>
      )}
      <p className="text-center text-sm text-muted mt-6">
        Nhớ ra mật khẩu? <Link to="/dang-nhap" className="text-primary font-semibold">Đăng nhập</Link>
      </p>
    </div>
  );
}
