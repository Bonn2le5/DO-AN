// Thông tin pháp lý dùng chung cho footer, Chính sách bảo mật và Điều khoản.
// Giá trị null = chưa có trong mã nguồn, chủ site phải tự điền; trang sẽ hiện ô [ĐIỀN: ...] màu vàng.

/** Tăng khi đổi nội dung Chính sách bảo mật; lưu kèm sự đồng ý của mỗi tài khoản (khoản 1, 2 Điều 6 NĐ 356/2025). */
export const PHIEN_BAN_CHINH_SACH = "1.0";
export const NGAY_CAP_NHAT_CHINH_SACH = "11/11/2026";

export const CHU_SO_HUU = {
  tenDonVi: null as string | null, // vd: "Hộ kinh doanh Mộc Kitchen" hoặc "Công ty TNHH ..."
  maSoThue: null as string | null,
  soDangKyKinhDoanh: null as string | null,
  diaChi: "236B Lê Văn Sỹ, Tân Sơn Hòa, TP.HCM",
  dienThoai: "+84 28 3822 1234",
  // Lấy từ footer. Tên miền khác mockitchen.id.vn trong render.yaml, cần xác nhận hộp thư này có người đọc.
  emailLienHe: "hello@moc-kitchen.vn",
  tenMien: "mockitchen.id.vn",
};
