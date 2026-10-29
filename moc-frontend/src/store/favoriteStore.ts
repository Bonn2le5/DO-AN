import { create } from "zustand";

interface FavoriteState {
  ids: Set<string>;
  toggle: (foodId: string) => void;
  isFavorite: (foodId: string) => boolean;
  count: () => number;
}

export const useFavoriteStore = create<FavoriteState>((set, get) => ({
  ids: new Set(["f3", "f6"]),
  toggle: (foodId) => {
    set((state) => {
      const next = new Set(state.ids);
      if (next.has(foodId)) next.delete(foodId);
      else next.add(foodId);
      return { ids: next };
    });
  },
  isFavorite: (foodId) => get().ids.has(foodId),
  count: () => get().ids.size,
}));
