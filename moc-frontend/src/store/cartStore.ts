import { create } from "zustand";
import type { CartItem, Food, Promotion } from "@/types";

interface CartState {
  // English properties
  items: CartItem[];
  isDrawerOpen: boolean;
  appliedPromo: Promotion | null;
  addItem: (food: Food, quantity?: number) => void;
  removeItem: (foodId: string) => void;
  updateQuantity: (foodId: string, quantity: number) => void;
  clearCart: () => void;
  openDrawer: () => void;
  closeDrawer: () => void;
  applyPromo: (promo: Promotion | null) => void;
  subtotal: () => number;
  discount: () => number;
  total: () => number;
  itemCount: () => number;

  // Vietnamese aliases
  danhSachMon: CartItem[];
  nganKeoMo: boolean;
  khuyenMaiApDung: Promotion | null;
  themMon: (monAn: Food, soLuong?: number) => void;
  xoaMon: (idMon: string) => void;
  capNhatSoLuong: (idMon: string, soLuong: number) => void;
  lamTrongGio: () => void;
  moNganKeo: () => void;
  dongNganKeo: () => void;
  apDungKhuyenMai: (khuyenMai: Promotion | null) => void;
  tinhTienHang: () => number;
  tinhTienGiam: () => number;
  tinhTongTien: () => number;
  demSoMon: () => number;
}

export const useCartStore = create<CartState>((set, get) => ({
  items: [],
  danhSachMon: [],
  isDrawerOpen: false,
  nganKeoMo: false,
  appliedPromo: null,
  khuyenMaiApDung: null,

  addItem: (food, quantity = 1) => {
    set((state) => {
      const existing = state.items.find((i) => i.food.id === food.id);
      let nextItems: CartItem[];
      if (existing) {
        nextItems = state.items.map((i) =>
          i.food.id === food.id ? { ...i, quantity: i.quantity + quantity, soLuong: (i.quantity ?? 1) + quantity } : i
        );
      } else {
        nextItems = [...state.items, { food, quantity, monAn: food, soLuong: quantity }];
      }
      return {
        items: nextItems,
        danhSachMon: nextItems,
        isDrawerOpen: true,
        nganKeoMo: true,
      };
    });
  },

  themMon: (monAn, soLuong = 1) => get().addItem(monAn, soLuong),

  removeItem: (foodId) => {
    set((state) => {
      const nextItems = state.items.filter((i) => i.food.id !== foodId);
      return { items: nextItems, danhSachMon: nextItems };
    });
  },

  xoaMon: (idMon) => get().removeItem(idMon),

  updateQuantity: (foodId, quantity) => {
    if (quantity <= 0) {
      get().removeItem(foodId);
      return;
    }
    set((state) => {
      const nextItems = state.items.map((i) =>
        i.food.id === foodId ? { ...i, quantity, soLuong: quantity } : i
      );
      return { items: nextItems, danhSachMon: nextItems };
    });
  },

  capNhatSoLuong: (idMon, soLuong) => get().updateQuantity(idMon, soLuong),

  clearCart: () => {
    set({ items: [], danhSachMon: [], appliedPromo: null, khuyenMaiApDung: null });
  },

  lamTrongGio: () => get().clearCart(),

  openDrawer: () => set({ isDrawerOpen: true, nganKeoMo: true }),
  moNganKeo: () => get().openDrawer(),

  closeDrawer: () => set({ isDrawerOpen: false, nganKeoMo: false }),
  dongNganKeo: () => get().closeDrawer(),

  applyPromo: (promo) => set({ appliedPromo: promo, khuyenMaiApDung: promo }),
  apDungKhuyenMai: (khuyenMai) => get().applyPromo(khuyenMai),

  subtotal: () => {
    return get().items.reduce((sum, item) => sum + (item.food.price ?? item.food.donGia ?? 0) * (item.quantity ?? item.soLuong ?? 1), 0);
  },
  tinhTienHang: () => get().subtotal(),

  discount: () => {
    const promo = get().appliedPromo;
    if (!promo) return 0;
    const sub = get().subtotal();
    const discountType = promo.discountType ?? promo.kieuGiamGia;
    const discountValue = Number(promo.discountValue ?? promo.giaTriGiam ?? 0);
    if (discountType === "percentage" || discountType === "phan_tram") {
      return Math.round((sub * discountValue) / 100);
    }
    return Math.min(sub, discountValue);
  },
  tinhTienGiam: () => get().discount(),

  total: () => {
    return Math.max(0, get().subtotal() - get().discount());
  },
  tinhTongTien: () => get().total(),

  itemCount: () => {
    return get().items.reduce((sum, item) => sum + (item.quantity ?? item.soLuong ?? 1), 0);
  },
  demSoMon: () => get().itemCount(),
}));
