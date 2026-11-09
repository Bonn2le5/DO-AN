import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { NguoiDung } from "@/types";
import { clearTokens } from "@/api/client";

interface AuthState {
  nguoiDung: NguoiDung | null;
  daDangNhap: boolean;
  dangNhap: (user: NguoiDung) => void;
  dangXuat: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      nguoiDung: null,
      daDangNhap: false,

      dangNhap: (user) => set({ nguoiDung: user, daDangNhap: true }),

      dangXuat: () => {
        clearTokens();
        set({ nguoiDung: null, daDangNhap: false });
      },
    }),
    {
      name: "moc_auth_storage",
      // v1: tên trường người dùng chuyển sang tiếng Việt; đổi dữ liệu đã lưu ở bản cũ.
      version: 1,
      migrate: (cu: any) => {
        const u = cu?.nguoiDung ?? cu?.user;
        const nguoiDung = u && {
          ...u,
          hoTen: u.hoTen ?? u.name,
          thuDienTu: u.thuDienTu ?? u.email,
          soDienThoai: u.soDienThoai ?? u.phone,
          kyTuDaiDien: u.kyTuDaiDien ?? u.avatarInitial,
          danhSachVaiTro: u.danhSachVaiTro ?? u.roles,
          laNhanVien: u.laNhanVien ?? u.isStaff,
          laQuanTri: u.laQuanTri ?? u.isAdmin,
          idChiNhanh: u.idChiNhanh ?? u.branchId,
        };
        return { nguoiDung: nguoiDung ?? null, daDangNhap: Boolean(cu?.daDangNhap ?? cu?.isAuthenticated) };
      },
    }
  )
);

// Token refresh can fail while the persisted Zustand session still says that
// the user is signed in. Keep the UI session in sync with the API session.
if (typeof window !== "undefined") {
  window.addEventListener("auth:expired", () => {
    useAuthStore.setState({
      nguoiDung: null,
      daDangNhap: false,
    });
  });
}
