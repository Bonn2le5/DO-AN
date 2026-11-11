import { create } from "zustand";
import { boYeuThich, ghiTuongTac } from "@/api/recommendations.api";

interface FavoriteState {
  ids: Set<string>;
  toggle: (foodId: string) => void;
  isFavorite: (foodId: string) => boolean;
  count: () => number;
}

export const useFavoriteStore = create<FavoriteState>((set, get) => ({
  ids: new Set(),
  toggle: (foodId) => {
    set((state) => {
      const next = new Set(state.ids);
      if (next.has(foodId)) {
        next.delete(foodId);
        boYeuThich(foodId);
      } else {
        next.add(foodId);
        ghiTuongTac(foodId, "yeu_thich"); // tín hiệu khẩu vị cho AI gợi ý (trọng số 2)
      }
      return { ids: next };
    });
  },
  isFavorite: (foodId) => get().ids.has(foodId),
  count: () => get().ids.size,
}));
