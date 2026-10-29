import { wait } from "../lib";

export interface Store<T extends { id: string }> {
  list(): Promise<T[]>;
  create(draft: Omit<T, "id">): Promise<T>;
  update(id: string, patch: Partial<T>): Promise<T>;
  remove(id: string): Promise<void>;
}

/**
 * Kho dữ liệu trong bộ nhớ, giả lập độ trễ mạng.
 * Khi nối backend: thay phần thân mỗi hàm bằng apiClient.get/post/patch/delete,
 * giữ nguyên chữ ký để các trang không phải sửa.
 */
export function createStore<T extends { id: string }>(seed: T[], prefix: string): Store<T> {
  let rows = [...seed];
  let counter = seed.length + 1;
  return {
    async list() {
      await wait();
      return [...rows];
    },
    async create(draft) {
      await wait(250);
      const row = { ...draft, id: `${prefix}${counter++}` } as T;
      rows = [row, ...rows];
      return row;
    },
    async update(id, patch) {
      await wait(250);
      const current = rows.find((r) => r.id === id);
      if (!current) throw new Error("Không tìm thấy bản ghi.");
      const next = { ...current, ...patch };
      rows = rows.map((r) => (r.id === id ? next : r));
      return next;
    },
    async remove(id) {
      await wait(250);
      rows = rows.filter((r) => r.id !== id);
    },
  };
}
