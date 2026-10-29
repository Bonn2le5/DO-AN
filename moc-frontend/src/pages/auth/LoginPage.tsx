import { useNavigate, Link, useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { login as loginApi } from "@/api/auth.api";
import { useAuthStore } from "@/store/authStore";

const schema = z.object({
  email: z.string().email("Email không hợp lệ"),
  password: z.string().min(6, "Mật khẩu tối thiểu 6 ký tự"),
});
type FormData = z.infer<typeof schema>;

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useAuthStore((s) => s.login);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    const result = await loginApi(data);
    login(result.user);
    if (result.user.isStaff) {
      navigate("/admin");
    } else {
      const destination = (location.state as { from?: string } | null)?.from;
      navigate(destination?.startsWith("/") ? destination : "/tai-khoan");
    }
  };

  return (
    <div className="max-w-md mx-auto px-5 py-20">
      <div className="text-center mb-9">
        <div className="font-display text-3xl mb-2">Chào mừng trở lại</div>
        <p className="text-muted text-sm">
          Đăng nhập để nhận gợi ý món ăn cá nhân hóa
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <input
            {...register("email")}
            type="email"
            placeholder="Email"
            className="w-full px-4 py-3.5 rounded-xl border border-black/15 text-sm outline-none focus:border-primary"
          />
          {errors.email && (
            <p className="text-xs text-primary mt-1.5">
              {errors.email.message}
            </p>
          )}
        </div>
        <div>
          <input
            {...register("password")}
            type="password"
            placeholder="Mật khẩu"
            className="w-full px-4 py-3.5 rounded-xl border border-black/15 text-sm outline-none focus:border-primary"
          />
          {errors.password && (
            <p className="text-xs text-primary mt-1.5">
              {errors.password.message}
            </p>
          )}
        </div>
        <button
          type="submit"
          disabled={isSubmitting}
          className="btn btn-primary w-full py-3.5!"
        >
          {isSubmitting ? "Đang đăng nhập..." : "Đăng nhập"}
        </button>
      </form>

      <p className="text-center text-sm text-muted mt-6">
        Chưa có tài khoản?{" "}
        <Link to="/dang-ky" className="text-primary font-semibold">
          Đăng ký ngay
        </Link>
      </p>
    </div>
  );
}
