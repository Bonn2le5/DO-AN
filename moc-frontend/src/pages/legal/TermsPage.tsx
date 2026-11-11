import { Link } from "react-router-dom";
import LegalLayout, { Dien, GiaTri, Muc } from "./LegalLayout";
import { CHU_SO_HUU, NGAY_CAP_NHAT_CHINH_SACH } from "@/lib/legal";

/*
 * BẢN NHÁP soạn từ mã nguồn ngày 11/11/2026. Cần người có chuyên môn pháp lý xem lại trước khi đăng.
 * Căn cứ: Luật Thương mại điện tử 122/2025/QH15 Điều 11 (công bố thông tin chủ sở hữu, quy chế, khiếu nại);
 * Luật Bảo vệ quyền lợi người tiêu dùng 19/2023/QH15 (Điều 25 cấm điều khoản miễn trừ trách nhiệm, Điều 31 khiếu nại).
 * Không thêm điều khoản miễn toàn bộ trách nhiệm hoặc hạn chế quyền khởi kiện của khách.
 */
export default function TermsPage() {
  const email = CHU_SO_HUU.emailLienHe;

  return (
    <LegalLayout title="Điều khoản sử dụng" updated={NGAY_CAP_NHAT_CHINH_SACH}>
      <Muc title="1. Thông tin chủ sở hữu website">
        <ul>
          <li>Đơn vị: <GiaTri value={CHU_SO_HUU.tenDonVi} ten="tên hộ kinh doanh / doanh nghiệp" /></li>
          <li>Mã số thuế: <GiaTri value={CHU_SO_HUU.maSoThue} ten="mã số thuế" /></li>
          <li>Số giấy chứng nhận đăng ký kinh doanh: <GiaTri value={CHU_SO_HUU.soDangKyKinhDoanh} ten="số ĐKKD, ngày cấp, nơi cấp" /></li>
          <li>Địa chỉ: {CHU_SO_HUU.diaChi}</li>
          <li>Email: <a href={`mailto:${email}`}>{email}</a> · Điện thoại: {CHU_SO_HUU.dienThoai}</li>
        </ul>
      </Muc>

      <Muc title="2. Tài khoản">
        <ul>
          <li>Bạn đăng ký bằng email và số điện thoại của chính mình, và xác thực email bằng mã gửi tới hộp thư.</li>
          <li>Bạn tự giữ mật khẩu. Nếu nghi tài khoản bị dùng trái phép, hãy đổi mật khẩu và báo cho chúng tôi.</li>
          <li>Dữ liệu của bạn được xử lý theo <Link to="/chinh-sach-bao-mat">Chính sách bảo vệ dữ liệu cá nhân</Link>.</li>
        </ul>
      </Muc>

      <Muc title="3. Đặt bàn">
        <ul>
          <li>Bạn chọn chi nhánh, ngày giờ, số khách và có thể gọi món trước. Nhà hàng gọi điện xác nhận đặt chỗ.</li>
          <li>Đặt bàn không gọi món trước thì không cần đặt cọc. Bạn gọi món và thanh toán tại nhà hàng.</li>
          <li>Bàn cụ thể do nhân viên xếp khi bạn đến.</li>
        </ul>
      </Muc>

      <Muc title="4. Đặt cọc và hoàn cọc">
        <ul>
          <li>
            Đặt bàn kèm gọi món trước cần cọc một phần tiền món. Số tiền, tỉ lệ cọc và thời hạn thanh toán hiện rõ
            ở bước xác nhận, trước khi bạn bấm đặt.
          </li>
          <li>Tiền cọc được trừ vào hóa đơn khi bạn dùng bữa.</li>
          <li>Thanh toán cọc qua PayOS (chuyển khoản / quét QR). Quá thời hạn mà chưa thanh toán thì chỗ giữ tạm được nhả cho khách khác.</li>
          <li>
            Tỉ lệ hoàn cọc khi hủy phụ thuộc vào thời điểm hủy so với giờ hẹn (trước 24 giờ, từ 6 đến 24 giờ, trong
            vòng 6 giờ, hoặc không đến). Mức cụ thể hiện trong mục "Xem điều kiện hoàn cọc" ở bước xác nhận đặt bàn
            và được áp dụng theo đúng mức đã hiện lúc bạn đặt.
          </li>
          <li>Tiền hoàn được chuyển khoản lại cho bạn. Thời hạn chuyển: <Dien>số ngày làm việc</Dien>.</li>
        </ul>
      </Muc>

      <Muc title="5. Trợ lý gọi món AI">
        <ul>
          <li>Trợ lý là phần mềm AI, không phải nhân viên. Thực đơn đề xuất chỉ để tham khảo; bạn tự quyết định món.</li>
          <li>Món, giá, khuyến mãi lấy từ thực đơn của nhà hàng. Giá áp dụng là giá hiện ở bước xác nhận đặt bàn.</li>
          <li>Lọc dị ứng có thể sót. Nếu có dị ứng hoặc yêu cầu ăn uống đặc biệt, hãy báo nhân viên khi đến.</li>
          <li>Cách dữ liệu được xử lý: xem <Link to="/chinh-sach-bao-mat#tro-ly-ai">Chính sách bảo mật, mục 4</Link>.</li>
        </ul>
      </Muc>

      <Muc title="6. Đánh giá và tin nhắn">
        <ul>
          <li>Đánh giá phải đúng trải nghiệm thật của bạn. Không đăng nội dung xúc phạm, quảng cáo hoặc thông tin cá nhân của người khác.</li>
          <li>Nhà hàng có thể ẩn đánh giá vi phạm các điều trên.</li>
        </ul>
      </Muc>

      {/* Căn cứ: Điều 31 khoản 2 Luật 19/2023/QH15: thông báo đã tiếp nhận trong 03 ngày làm việc. */}
      <Muc title="7. Khiếu nại và giải quyết tranh chấp">
        <ul>
          <li>Gửi phản ánh, khiếu nại qua email <a href={`mailto:${email}`}>{email}</a>, điện thoại {CHU_SO_HUU.dienThoai} hoặc khung chat trên website.</li>
          <li>Chúng tôi báo đã tiếp nhận trong 03 ngày làm việc và trả lời kết quả trong <Dien>số ngày</Dien>.</li>
          <li>Hai bên ưu tiên thương lượng. Nếu không thống nhất được, bạn có quyền yêu cầu cơ quan bảo vệ người tiêu dùng, hòa giải, trọng tài hoặc tòa án giải quyết theo quy định pháp luật.</li>
        </ul>
      </Muc>
    </LegalLayout>
  );
}
