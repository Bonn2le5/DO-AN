import { useNavigate, Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { register as registerApi } from "@/api/auth.api";

const schema = z
  .object({
    name: z.string().min(2, "Vui lòng nhập họ tên"),
    email: z.string().email("Email không hợp lệ"),
    phone: z.string().regex(/^(0|\+84)\d{9,10}$/, "Số điện thoại không hợp lệ"),
    password: z.string().min(6, "Mật khẩu tối thiểu 6 ký tự"),
    confirmPassword: z.string(),
    // Không tích sẵn (khoản 3 Điều 6 NĐ 356/2025); bắt buộc để tạo tài khoản.
    agree: z.boolean().refine((v) => v, "Vui lòng đồng ý để tạo tài khoản"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Mật khẩu xác nhận không khớp",
    path: ["confirmPassword"],
  });
type FormData = z.infer<typeof schema>;

export default function RegisterPage() {
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema), defaultValues: { agree: false } });

  const onSubmit = async (data: FormData) => {
    try {
      const result = await registerApi(data);
      // Backend requires email verification before login
      navigate(`/xac-thuc-email?email=${encodeURIComponent(result.email)}`);
    } catch (e: any) {
      const body = e.response?.data;
      const message = body && typeof body === "object" ? Object.values(body).flat()[0] : null;
      setError("root", { message: String(message ?? "Đăng ký thất bại, vui lòng thử lại.") });
    }
  };

  return (
    <div className="max-w-md mx-auto px-5 py-16">
      <div className="text-center mb-9">
        <div className="font-display text-3xl mb-2">Tạo tài khoản mới</div>
        <p className="text-muted text-sm">
          Lưu lịch đặt bàn, món yêu thích và nhận gợi ý món theo khẩu vị
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <input
            {...register("name")}
            placeholder="Họ và tên"
            className="w-full px-4 py-3.5 rounded-xl border border-black/15 text-sm outline-none focus:border-primary"
          />
          {errors.name && (
            <p className="text-xs text-primary mt-1.5">{errors.name.message}</p>
          )}
        </div>
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
            {...register("phone")}
            placeholder="Số điện thoại"
            className="w-full px-4 py-3.5 rounded-xl border border-black/15 text-sm outline-none focus:border-primary"
          />
          {errors.phone && (
            <p className="text-xs text-primary mt-1.5">
              {errors.phone.message}
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
        <div>
          <input
            {...register("confirmPassword")}
            type="password"
            placeholder="Xác nhận mật khẩu"
            className="w-full px-4 py-3.5 rounded-xl border border-black/15 text-sm outline-none focus:border-primary"
          />
          {errors.confirmPassword && (
            <p className="text-xs text-primary mt-1.5">
              {errors.confirmPassword.message}
            </p>
          )}
        </div>
        <div>
          <label className="flex gap-2.5 items-start text-[13px] leading-relaxed text-muted cursor-pointer">
            <input
              {...register("agree")}
              type="checkbox"
              className="mt-[3px] h-4 w-4 shrink-0 accent-[var(--color-primary)]"
            />
            <span>
              Tôi đồng ý để nhà hàng Mộc dùng họ tên, email, số điện thoại để tạo tài khoản, xác thực email và quản lý
              đặt bàn, theo{" "}
              <Link to="/chinh-sach-bao-mat" target="_blank" className="text-primary underline underline-offset-2">Chính sách bảo vệ dữ liệu cá nhân</Link>
              {" "}và{" "}
              <Link to="/dieu-khoan" target="_blank" className="text-primary underline underline-offset-2">Điều khoản sử dụng</Link>.
            </span>
          </label>
          {errors.agree && (
            <p className="text-xs text-primary mt-1.5">{errors.agree.message}</p>
          )}
        </div>
        {errors.root && (
          <p className="text-sm text-primary text-center">{errors.root.message}</p>
        )}
        <button
          type="submit"
          disabled={isSubmitting}
          className="btn btn-primary w-full py-3.5!"
        >
          {isSubmitting ? "Đang tạo tài khoản..." : "Đăng ký"}
        </button>
      </form>

      <p className="text-center text-sm text-muted mt-6">
        Đã có tài khoản?{" "}
        <Link to="/dang-nhap" className="text-primary font-semibold">
          Đăng nhập
        </Link>
      </p>
    </div>
  );
}
