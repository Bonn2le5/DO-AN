import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";
import { clearTokens } from "@/api/client";

interface AuthState {
  // English properties
  user: User | null;
  isAuthenticated: boolean;
  login: (user: User) => void;
  logout: () => void;

  // Vietnamese aliases
  nguoiDung: User | null;
  daDangNhap: boolean;
  dangNhap: (user: User) => void;
  dangXuat: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      nguoiDung: null,
      isAuthenticated: false,
      daDangNhap: false,

      login: (user) => set({ user, nguoiDung: user, isAuthenticated: true, daDangNhap: true }),
      dangNhap: (user) => set({ user, nguoiDung: user, isAuthenticated: true, daDangNhap: true }),

      logout: () => {
        clearTokens();
        set({ user: null, nguoiDung: null, isAuthenticated: false, daDangNhap: false });
      },
      dangXuat: () => {
        clearTokens();
        set({ user: null, nguoiDung: null, isAuthenticated: false, daDangNhap: false });
      },
    }),
    {
      name: "moc_auth_storage",
    }
  )
);
