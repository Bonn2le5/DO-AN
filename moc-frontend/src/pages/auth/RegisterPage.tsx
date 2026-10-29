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
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    const result = await registerApi(data);
    // Backend requires email verification before login
    navigate(`/auth/verify-email?email=${encodeURIComponent(result.email)}`);
  };

  return (
    <div className="max-w-md mx-auto px-5 py-16">
      <div className="text-center mb-9">
        <div className="font-display text-3xl mb-2">Tạo tài khoản mới</div>
        <p className="text-muted text-sm">
          Nhận ưu đãi và gợi ý món ăn dành riêng cho bạn
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
