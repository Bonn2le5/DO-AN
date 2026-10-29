import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { verifyEmail, resendVerificationEmail } from "@/api/auth.api";
import { useAuthStore } from "@/store/authStore";

export default function EmailVerificationPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const login = useAuthStore((s) => s.login);

  const email = searchParams.get("email") ?? "";
  const [otp, setOtp] = useState("");
  const [verifying, setVerifying] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState("");
  const [resendSuccess, setResendSuccess] = useState(false);

  const handleVerify = async () => {
    if (!otp || otp.length !== 6) {
      setError("Vui lòng nhập mã 6 chữ số.");
      return;
    }
    setError("");
    setVerifying(true);
    try {
      const result = await verifyEmail({ email, maXacThuc: otp });
      login(result.user);
      navigate("/tai-khoan");
    } catch (e: any) {
      setError(
        e.response?.data?.detail ??
          "Mã xác thực không đúng hoặc đã hết hạn. Vui lòng thử lại."
      );
    } finally {
      setVerifying(false);
    }
  };

  const handleResend = async () => {
    setResending(true);
    setResendSuccess(false);
    setError("");
    try {
      await resendVerificationEmail(email);
      setResendSuccess(true);
    } catch (e: any) {
      setError(e.response?.data?.detail ?? "Không thể gửi lại mã. Vui lòng thử lại.");
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-5 py-16">
      <div className="text-center mb-9">
        <div className="text-5xl mb-4">📧</div>
        <div className="font-display text-3xl mb-2">Xác thực email</div>
        <p className="text-muted text-sm">
          Chúng tôi đã gửi mã xác thực 6 chữ số đến
          <br />
          <span className="font-semibold text-dark">{email}</span>
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="text-xs font-bold uppercase tracking-wide text-muted block mb-1.5">
            Mã xác thực
          </label>
          <input
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength={6}
            value={otp}
            onChange={(e) => {
              setOtp(e.target.value.replace(/\D/g, ""));
              setError("");
            }}
            placeholder="Nhập mã 6 chữ số"
            className="w-full px-4 py-3.5 rounded-xl border border-black/15 text-sm outline-none focus:border-primary text-center tracking-[0.5em] text-lg font-bold"
          />
          {error && (
            <p className="text-xs text-primary mt-1.5">{error}</p>
          )}
        </div>

        <button
          onClick={handleVerify}
          disabled={verifying || otp.length !== 6}
          className="btn btn-primary w-full py-3.5!"
        >
          {verifying ? "Đang xác thực..." : "Xác thực"}
        </button>

        <div className="text-center">
          {resendSuccess ? (
            <p className="text-sm text-green-600">✓ Đã gửi lại mã thành công!</p>
          ) : (
            <button
              onClick={handleResend}
              disabled={resending}
              className="text-sm text-primary font-semibold hover:underline disabled:opacity-50"
            >
              {resending ? "Đang gửi..." : "Gửi lại mã"}
            </button>
          )}
        </div>

        <p className="text-center text-sm text-muted">
          Mã có hiệu lực trong 15 phút. Kiểm tra thư mục Spam nếu không thấy email.
        </p>
      </div>
    </div>
  );
}
