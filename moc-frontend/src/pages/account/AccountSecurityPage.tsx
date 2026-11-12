import { useState } from "react";
import { useForm } from "react-hook-form";
import { useAuthStore } from "@/store/authStore";
import { apiErrorMessage, changePassword, confirmEmailChange, requestEmailChange } from "@/api/auth.api";

const INPUT = "w-full px-4 py-3 rounded-xl border border-black/15 text-sm outline-none focus:border-primary";
const LABEL = "text-xs font-semibold text-muted block mb-1.5";

interface PasswordForm { oldPassword: string; newPassword: string; confirm: string }
interface EmailForm { email: string; password: string }

function PasswordCard() {
  const { register, handleSubmit, reset, setError, formState: { errors, isSubmitting, isSubmitSuccessful } } =
    useForm<PasswordForm>();

  const onSubmit = async (d: PasswordForm) => {
    try {
      await changePassword(d.oldPassword, d.newPassword);
      reset(undefined, { keepIsSubmitSuccessful: true });
    } catch (e) {
      setError("root", { message: apiErrorMessage(e, "Đổi mật khẩu thất bại.") });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="card p-7 space-y-4">
      <h2 className="font-display text-xl">Đổi mật khẩu</h2>
      <div>
        <label className={LABEL} htmlFor="old-pw">Mật khẩu hiện tại</label>
        <input id="old-pw" type="password" autoComplete="current-password" className={INPUT}
          {...register("oldPassword", { required: "Nhập mật khẩu hiện tại." })} />
        {errors.oldPassword && <p className="text-xs text-red-600 mt-1">{errors.oldPassword.message}</p>}
      </div>
      <div>
        <label className={LABEL} htmlFor="new-pw">Mật khẩu mới</label>
        <input id="new-pw" type="password" autoComplete="new-password" className={INPUT}
          {...register("newPassword", { minLength: { value: 6, message: "Tối thiểu 6 ký tự." }, required: "Nhập mật khẩu mới." })} />
        {errors.newPassword && <p className="text-xs text-red-600 mt-1">{errors.newPassword.message}</p>}
      </div>
      <div>
        <label className={LABEL} htmlFor="confirm-pw">Nhập lại mật khẩu mới</label>
        <input id="confirm-pw" type="password" autoComplete="new-password" className={INPUT}
          {...register("confirm", { validate: (v, f) => v === f.newPassword || "Mật khẩu nhập lại không khớp." })} />
        {errors.confirm && <p className="text-xs text-red-600 mt-1">{errors.confirm.message}</p>}
      </div>
      {errors.root && <p className="text-sm text-red-600">{errors.root.message}</p>}
      {isSubmitSuccessful && !errors.root && <p className="text-sm text-emerald-700">Đã đổi mật khẩu.</p>}
      <button type="submit" disabled={isSubmitting} className="btn btn-primary">
        {isSubmitting ? "Đang lưu..." : "Đổi mật khẩu"}
      </button>
    </form>
  );
}

function EmailCard() {
  const { nguoiDung: user, dangNhap: login } = useAuthStore();
  const { register, handleSubmit, reset, resetField, setError, formState: { errors, isSubmitting } } =
    useForm<EmailForm>({ defaultValues: { email: user?.thuDienTu ?? "" } });
  const [pending, setPending] = useState("");
  const [code, setCode] = useState("");
  const [codeError, setCodeError] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [done, setDone] = useState(false);

  const onSubmit = async (d: EmailForm) => {
    try {
      const email = await requestEmailChange(d.email.trim(), d.password);
      resetField("password");
      if (!email) return setError("root", { message: "Email mới trùng với email hiện tại." });
      setPending(email); setCode(""); setCodeError(""); setDone(false);
    } catch (e) {
      setError("root", { message: apiErrorMessage(e, "Cập nhật email thất bại.") });
    }
  };

  const onConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    setConfirming(true);
    try {
      const updated = await confirmEmailChange(code);
      login(updated);
      reset({ email: updated.thuDienTu ?? "", password: "" });
      setPending(""); setDone(true);
    } catch (err) {
      setCodeError(apiErrorMessage(err, "Xác nhận thất bại."));
    } finally {
      setConfirming(false);
    }
  };

  if (pending) {
    return (
      <form key="code" onSubmit={onConfirm} className="card p-7 space-y-4">
        <h2 className="font-display text-xl">Xác nhận email mới</h2>
        <p className="text-sm text-muted">
          Đã gửi mã 6 số tới <strong className="text-dark">{pending}</strong>. Mã có hiệu lực 15 phút.
        </p>
        <div>
          <label className={LABEL} htmlFor="email-code">Mã xác thực</label>
          <input id="email-code" inputMode="numeric" autoComplete="one-time-code" maxLength={6} className={INPUT}
            value={code} onChange={(e) => { setCode(e.target.value.replace(/\D/g, "")); setCodeError(""); }} />
          {codeError && <p className="text-xs text-red-600 mt-1">{codeError}</p>}
        </div>
        <div className="flex gap-3">
          <button type="submit" disabled={confirming || code.length !== 6} className="btn btn-primary">
            {confirming ? "Đang xác nhận..." : "Xác nhận"}
          </button>
          <button type="button" onClick={() => setPending("")} className="btn">Huỷ</button>
        </div>
      </form>
    );
  }

  return (
    <form key="email" onSubmit={handleSubmit(onSubmit)} className="card p-7 space-y-4">
      <h2 className="font-display text-xl">Cập nhật email</h2>
      <p className="text-sm text-muted">Email dùng để đăng nhập và nhận xác nhận đặt bàn. Chúng tôi sẽ gửi mã xác thực tới email mới.</p>
      <div>
        <label className={LABEL} htmlFor="email">Email mới</label>
        <input id="email" type="email" autoComplete="email" className={INPUT}
          {...register("email", { required: "Nhập email." })} />
      </div>
      <div>
        <label className={LABEL} htmlFor="email-pw">Mật khẩu hiện tại</label>
        <input id="email-pw" type="password" autoComplete="current-password" className={INPUT}
          {...register("password", { required: "Nhập mật khẩu để xác nhận." })} />
        {errors.password && <p className="text-xs text-red-600 mt-1">{errors.password.message}</p>}
      </div>
      {errors.root && <p className="text-sm text-red-600">{errors.root.message}</p>}
      {done && !errors.root && <p className="text-sm text-emerald-700">Đã cập nhật email.</p>}
      <button type="submit" disabled={isSubmitting} className="btn btn-primary">
        {isSubmitting ? "Đang gửi mã..." : "Cập nhật email"}
      </button>
    </form>
  );
}

export default function AccountSecurityPage() {
  return (
    <div className="space-y-6 max-w-lg">
      <PasswordCard />
      <EmailCard />
    </div>
  );
}
