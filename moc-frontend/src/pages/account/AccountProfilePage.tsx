import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { apiErrorMessage, updateProfile } from "@/api/auth.api";

interface ProfileForm {
  name: string;
  phone: string;
}

export default function AccountProfilePage() {
  const { user, login } = useAuthStore();
  const { register, handleSubmit, setError, formState: { errors, isSubmitting, isSubmitSuccessful } } = useForm<ProfileForm>({
    defaultValues: { name: user?.name ?? "", phone: user?.phone ?? "" },
  });

  const onSubmit = async (data: ProfileForm) => {
    // Backend lưu họ tên theo first_name + last_name.
    const [first, ...rest] = data.name.trim().split(/\s+/);
    try {
      login(await updateProfile({ first_name: first ?? "", last_name: rest.join(" "), so_dien_thoai: data.phone.trim() }));
    } catch (e) {
      setError("root", { message: apiErrorMessage(e, "Lưu thất bại, vui lòng thử lại.") });
    }
  };

  return (
    <div className="card p-7 max-w-lg">
      <h2 className="font-display text-xl mb-6">Thông tin cá nhân</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label htmlFor="pf-name" className="text-xs font-semibold text-muted block mb-1.5">Họ và tên</label>
          <input id="pf-name" {...register("name", { required: true })} className="w-full px-4 py-3 rounded-xl border border-black/15 text-sm outline-none focus:border-primary" />
        </div>
        <div>
          <label htmlFor="pf-email" className="text-xs font-semibold text-muted block mb-1.5">Email</label>
          <input id="pf-email" value={user?.email ?? ""} readOnly className="w-full px-4 py-3 rounded-xl border border-black/10 bg-black/[0.03] text-sm text-muted" />
          <p className="text-xs text-muted mt-1.5">
            Đổi email tại <Link to="/tai-khoan/bao-mat" className="text-primary font-medium">Bảo mật</Link>.
          </p>
        </div>
        <div>
          <label htmlFor="pf-phone" className="text-xs font-semibold text-muted block mb-1.5">Số điện thoại</label>
          <input id="pf-phone" type="tel" {...register("phone")} className="w-full px-4 py-3 rounded-xl border border-black/15 text-sm outline-none focus:border-primary" />
        </div>
        {errors.root && <p className="text-sm text-red-600">{errors.root.message}</p>}
        {isSubmitSuccessful && !errors.root && <p className="text-sm text-emerald-700">Đã lưu thay đổi.</p>}
        <button type="submit" disabled={isSubmitting} className="btn btn-primary">
          {isSubmitting ? "Đang lưu..." : "Lưu thay đổi"}
        </button>
      </form>
    </div>
  );
}
