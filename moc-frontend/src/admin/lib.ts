export const wait = (ms = 350) => new Promise<void>((r) => setTimeout(r, ms));

export const ymd = (offsetDays = 0) => {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
};

export const ago = (minutes: number) => new Date(Date.now() - minutes * 60000).toISOString();

export const fmtDateTime = (iso: string) =>
  new Date(iso).toLocaleString("vi-VN", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });

export const fmtShort = (n: number) =>
  n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1).replace(".0", "")}tr` : n >= 1000 ? `${Math.round(n / 1000)}k` : String(n);

export const lineTotal = (items: { qty: number; price: number }[]) =>
  items.reduce((s, i) => s + i.qty * i.price, 0);
