import { ago, ymd } from "../lib";

export interface AdminFood {
  id: string; name: string; category: string; price: number; stock: number; available: boolean;
  spicy: number; vegetarian: boolean; trackInventory: boolean; description: string; image?: string; tone: number; rating: number;
}
export interface AdminCategory { id: string; name: string; description: string; active: boolean }
export interface AdminTag { id: string; name: string }
export interface AdminIngredient { id: string; name: string; unit: string; currentStock: number; minimumStock: number; active: boolean }
export interface AdminPromotion {
  id: string; code: string; name: string; discountType: "percent" | "fixed"; discountValue: number; minOrder: number;
  maxDiscount: number; startAt: string; endAt: string; usageLimit: number; usedCount: number; active: boolean;
}
export interface AdminPost { id: string; title: string; category: string; status: "draft" | "published" | "archived"; content: string; image?: string; createdAt: string }
export interface AdminReview { id: string; food: string; customer: string; rating: number; comment: string; visible: boolean; createdAt: string }
export interface AdminUser { id: string; name: string; email: string; phone: string; role: "admin" | "staff" | "customer"; active: boolean; createdAt: string; password?: string }
export interface AdminBranch { id: string; name: string; address: string; phone: string; lat: number; lng: number; active: boolean }

export const CATEGORY_OPTIONS = ["Món chính", "Khai vị", "Đồ uống", "Tráng miệng", "Combo"].map((v) => ({ value: v, label: v }));

const F = (n: number, name: string, category: string, price: number, stock: number, spicy: number, veg: boolean, available: boolean, rating: number, description: string): AdminFood => ({
  id: `f${n}`, name, category, price, stock, spicy, vegetarian: veg, available, trackInventory: false, description, tone: (n % 6) + 1, rating,
});

export const foodsSeed: AdminFood[] = [
  F(1, "Bò lúc lắc sốt tiêu", "Món chính", 189000, 32, 1, false, true, 4.9, "Thịt bò Úc áp chảo, sốt tiêu đen cay nhẹ"),
  F(2, "Gỏi cuốn tôm thịt", "Khai vị", 69000, 40, 0, false, true, 4.8, "Bánh tráng cuốn tươi, chấm sốt me chua ngọt"),
  F(3, "Lẩu Thái hải sản", "Món chính", 259000, 18, 3, false, true, 5.0, "Tôm, mực, nghêu tươi trong nước lẩu chua cay"),
  F(4, "Trà đào cam sả", "Đồ uống", 45000, 60, 0, true, true, 4.7, "Trà thủ công, đào tươi, thơm mùi sả"),
  F(5, "Chè khúc bạch nhãn", "Tráng miệng", 39000, 25, 0, true, true, 4.9, "Khúc bạch mềm mịn, nhãn tươi, hạnh nhân"),
  F(6, "Cơm tấm sườn bì chả", "Món chính", 75000, 45, 0, false, true, 4.8, "Sườn nướng than hoa, bì, chả trứng hấp"),
  F(7, "Bún chả Hà Nội", "Món chính", 79000, 30, 1, false, true, 4.85, "Chả viên và chả miếng nướng than"),
  F(8, "Nộm đu đủ chay", "Khai vị", 55000, 0, 2, true, false, 4.6, "Đu đủ bào sợi, đậu phộng, sốt chua cay chay"),
];

export const categoriesSeed: AdminCategory[] = [
  { id: "c1", name: "Món chính", description: "Các món no, dùng cho bữa chính", active: true },
  { id: "c2", name: "Khai vị", description: "Món nhẹ dùng trước bữa ăn", active: true },
  { id: "c3", name: "Đồ uống", description: "Trà, nước ép, sinh tố", active: true },
  { id: "c4", name: "Tráng miệng", description: "Chè, bánh, trái cây", active: true },
  { id: "c5", name: "Combo", description: "Set ăn tiết kiệm", active: false },
];
export const tagsSeed: AdminTag[] = ["Món mới", "Bán chạy", "Đặc biệt", "Ăn chay"].map((name, i) => ({ id: `tg${i + 1}`, name }));

export const ingredientsSeed: AdminIngredient[] = [
  { id: "i1", name: "Thịt bò thăn Úc", unit: "kg", currentStock: 18, minimumStock: 10, active: true },
  { id: "i2", name: "Tôm sú", unit: "kg", currentStock: 6, minimumStock: 8, active: true },
  { id: "i3", name: "Mực ống", unit: "kg", currentStock: 9, minimumStock: 5, active: true },
  { id: "i4", name: "Sả", unit: "kg", currentStock: 3, minimumStock: 4, active: true },
  { id: "i5", name: "Bún tươi", unit: "kg", currentStock: 25, minimumStock: 12, active: true },
  { id: "i6", name: "Trà đen", unit: "kg", currentStock: 7, minimumStock: 3, active: true },
  { id: "i7", name: "Nhãn lồng", unit: "kg", currentStock: 2, minimumStock: 5, active: true },
  { id: "i8", name: "Nước tương lên men", unit: "l", currentStock: 14, minimumStock: 6, active: true },
];

const iso = (off: number, h: number) => `${ymd(off)}T${String(h).padStart(2, "0")}:00`;
export const promotionsSeed: AdminPromotion[] = [
  { id: "pr1", code: "WELCOME20", name: "Giảm cho đơn đầu tiên", discountType: "percent", discountValue: 20, minOrder: 0, maxDiscount: 80000, startAt: iso(-30, 0), endAt: iso(20, 23), usageLimit: 500, usedCount: 212, active: true },
  { id: "pr2", code: "SAVE50", name: "Đơn từ 300.000đ", discountType: "fixed", discountValue: 50000, minOrder: 300000, maxDiscount: 0, startAt: iso(-10, 0), endAt: iso(5, 23), usageLimit: 300, usedCount: 281, active: true },
  { id: "pr3", code: "WEEKEND", name: "Combo cuối tuần", discountType: "fixed", discountValue: 0, minOrder: 0, maxDiscount: 0, startAt: iso(-60, 0), endAt: iso(60, 23), usageLimit: 0, usedCount: 87, active: true },
  { id: "pr4", code: "TET2026", name: "Đón Tết sớm", discountType: "percent", discountValue: 15, minOrder: 200000, maxDiscount: 100000, startAt: iso(60, 0), endAt: iso(90, 23), usageLimit: 1000, usedCount: 0, active: false },
];

export const postsSeed: AdminPost[] = [
  { id: "b1", title: "Bí quyết chọn nguyên liệu tươi mỗi sáng tại chợ đầu mối", category: "Ẩm thực", status: "published", content: "Mỗi sáng lúc 4 giờ, bếp trưởng của MỘC đã có mặt tại chợ đầu mối…", createdAt: ago(60 * 24 * 12) },
  { id: "b2", title: "MỘC khai trương chi nhánh thứ 3 tại Quận 7", category: "Sự kiện", status: "published", content: "Sau 12 năm phát triển, MỘC chính thức khai trương chi nhánh thứ 3…", createdAt: ago(60 * 24 * 19) },
  { id: "b3", title: "3 cách biến tấu món gỏi cuốn cho ngày hè", category: "Công thức", status: "draft", content: "Gỏi cuốn là món ăn quen thuộc nhưng luôn có thể biến tấu…", createdAt: ago(60 * 24 * 2) },
];

export const reviewsSeed: AdminReview[] = [
  { id: "v1", food: "Bò lúc lắc sốt tiêu", customer: "Lan Anh", rating: 5, comment: "Bò mềm, sốt tiêu vừa miệng, đóng gói giữ nhiệt rất tốt.", visible: true, createdAt: ago(60 * 24 * 2) },
  { id: "v2", food: "Lẩu Thái hải sản", customer: "Minh Tân", rating: 5, comment: "Nước lẩu chuẩn vị, hải sản tươi.", visible: true, createdAt: ago(60 * 24 * 4) },
  { id: "v3", food: "Bò lúc lắc sốt tiêu", customer: "Hoài Thương", rating: 4, comment: "Ngon nhưng hơi mặn với mình.", visible: true, createdAt: ago(60 * 24 * 6) },
  { id: "v4", food: "Cơm tấm sườn bì chả", customer: "Quốc Bảo", rating: 1, comment: "Giao trễ gần một tiếng, món nguội.", visible: false, createdAt: ago(60 * 24 * 7) },
  { id: "v5", food: "Chè khúc bạch nhãn", customer: "Mỹ Linh", rating: 5, comment: "Mát, ngọt vừa, hạnh nhân giòn.", visible: true, createdAt: ago(60 * 24 * 9) },
];

export const usersSeed: AdminUser[] = [
  { id: "u1", name: "Nguyễn Văn Vũ", email: "admin@moc.vn", phone: "0901 000 001", role: "admin", active: true, createdAt: ago(60 * 24 * 200) },
  { id: "u2", name: "Lê Thu Hà", email: "leTan@moc.vn", phone: "0901 000 002", role: "staff", active: true, createdAt: ago(60 * 24 * 120) },
  { id: "u3", name: "Phạm Quang Huy", email: "cskh@moc.vn", phone: "0901 000 003", role: "staff", active: true, createdAt: ago(60 * 24 * 90) },
  { id: "u4", name: "Nguyễn Lan Anh", email: "lananh@gmail.com", phone: "0903 112 233", role: "customer", active: true, createdAt: ago(60 * 24 * 40) },
  { id: "u5", name: "Trần Minh Tân", email: "minhtan@gmail.com", phone: "0987 654 321", role: "customer", active: true, createdAt: ago(60 * 24 * 22) },
  { id: "u6", name: "Bùi Khánh Ly", email: "khanhly@gmail.com", phone: "0944 567 890", role: "customer", active: false, createdAt: ago(60 * 24 * 10) },
];

export const branchesSeed: AdminBranch[] = [
  { id: "br1", name: "MỘC — Chi nhánh Lê Văn Sỹ", address: "236B Lê Văn Sỹ, Tân Sơn Hòa, TP.HCM", phone: "028 3822 1234", lat: 10.7924, lng: 106.6803, active: true },
  { id: "br2", name: "MỘC — Chi nhánh Quận 7", address: "Số 8 Nguyễn Lương Bằng, Tân Phú, Quận 7", phone: "028 3822 5678", lat: 10.7297, lng: 106.7217, active: true },
  { id: "br3", name: "MỘC — Chi nhánh Thảo Điền", address: "12 Quốc Hương, Thảo Điền, TP. Thủ Đức", phone: "028 3822 9012", lat: 10.8033, lng: 106.7378, active: true },
];
