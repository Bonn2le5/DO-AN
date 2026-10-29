import { useForm } from "react-hook-form";
import { useAuthStore } from "@/store/authStore";

interface ProfileForm {
  name: string;
  email: string;
  phone: string;
}

export default function AccountProfilePage() {
  const user = useAuthStore((s) => s.user);
  const { register, handleSubmit, formState: { isSubmitting } } = useForm<ProfileForm>({
    defaultValues: { name: user?.name ?? "", email: user?.email ?? "", phone: user?.phone ?? "" },
  });

  const onSubmit = async (data: ProfileForm) => {
    // TODO(backend): PATCH /api/users/me/
    await new Promise((r) => setTimeout(r, 500));
    console.log("Profile updated", data);
  };

  return (
    <div className="card p-7 max-w-lg">
      <h2 className="font-display text-xl mb-6">Thông tin cá nhân</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="text-xs font-semibold text-muted block mb-1.5">Họ và tên</label>
          <input {...register("name")} className="w-full px-4 py-3 rounded-xl border border-black/15 text-sm outline-none focus:border-primary" />
        </div>
        <div>
          <label className="text-xs font-semibold text-muted block mb-1.5">Email</label>
          <input {...register("email")} type="email" className="w-full px-4 py-3 rounded-xl border border-black/15 text-sm outline-none focus:border-primary" />
        </div>
        <div>
          <label className="text-xs font-semibold text-muted block mb-1.5">Số điện thoại</label>
          <input {...register("phone")} className="w-full px-4 py-3 rounded-xl border border-black/15 text-sm outline-none focus:border-primary" />
        </div>
        <button type="submit" disabled={isSubmitting} className="btn btn-primary">
          {isSubmitting ? "Đang lưu..." : "Lưu thay đổi"}
        </button>
      </form>
    </div>
  );
}
