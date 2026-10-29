import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...values: ClassValue[]) {
  return twMerge(clsx(values));
}

export function formatCurrency(amount: number) {
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatDate(value: string | Date) {
  return new Intl.DateTimeFormat("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" }).format(new Date(value));
}

export function localDateInputValue() {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60_000)
    .toISOString()
    .slice(0, 10);
}

const FOOD_TONES = [
  "linear-gradient(135deg, #f6bd60, #f28482)",
  "linear-gradient(135deg, #84a59d, #f6bd60)",
  "linear-gradient(135deg, #f28482, #f7ede2)",
  "linear-gradient(135deg, #a8dadc, #457b9d)",
];

export function toneGradient(tone: number) {
  return FOOD_TONES[Math.abs(Math.trunc(tone)) % FOOD_TONES.length];
}
