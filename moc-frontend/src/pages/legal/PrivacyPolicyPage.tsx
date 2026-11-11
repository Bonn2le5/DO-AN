import { Link } from "react-router-dom";
import LegalLayout, { Bang, Dien, GiaTri, Muc } from "./LegalLayout";
import { CHU_SO_HUU, NGAY_CAP_NHAT_CHINH_SACH, PHIEN_BAN_CHINH_SACH } from "@/lib/legal";

/*
 * BẢN NHÁP soạn từ mã nguồn ngày 11/11/2026 bằng bộ checklist vn-law-check.
 * Mỗi dòng dữ liệu, mỗi bên nhận đều lấy từ code (form, model, API gọi ra ngoài).
 * Cần người có chuyên môn pháp lý xem lại và điền các ô [ĐIỀN] trước khi đăng chính thức.
 * Căn cứ chính: Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15, Nghị định 356/2025/NĐ-CP.
 * Khi đổi nội dung, tăng PHIEN_BAN_CHINH_SACH trong src/lib/legal.ts.
 */
export default function PrivacyPolicyPage() {
  const email = CHU_SO_HUU.emailLienHe;

  return (
    <LegalLayout title="Chính sách bảo vệ dữ liệu cá nhân" updated={NGAY_CAP_NHAT_CHINH_SACH} version={PHIEN_BAN_CHINH_SACH}>
      <p>
        Trang này giải thích nhà hàng Mộc thu thập dữ liệu gì của bạn khi dùng website {CHU_SO_HUU.tenMien},
        dùng để làm gì, gửi cho ai, lưu ở đâu và bạn có những quyền gì. Chúng tôi viết ngắn gọn để bạn đọc hết được.
      </p>

      {/* Căn cứ: điểm b khoản 2 Điều 9 Luật 91/2025: người dùng phải biết bên kiểm soát dữ liệu. */}
      <Muc title="1. Chúng tôi là ai">
        <p>
          <GiaTri value={CHU_SO_HUU.tenDonVi} ten="tên hộ kinh doanh / doanh nghiệp" /> (sau đây gọi là "chúng tôi")
          là bên quyết định việc thu thập và sử dụng dữ liệu cá nhân trên website này.
        </p>
        <ul>
          <li>Mã số thuế / số đăng ký kinh doanh: <GiaTri value={CHU_SO_HUU.maSoThue} ten="mã số thuế" /></li>
          <li>Địa chỉ: {CHU_SO_HUU.diaChi}</li>
          <li>Email tiếp nhận yêu cầu về dữ liệu cá nhân: <a href={`mailto:${email}`}>{email}</a></li>
          <li>Điện thoại: {CHU_SO_HUU.dienThoai}</li>
        </ul>
      </Muc>

      {/* Căn cứ: Điều 9 khoản 2 điểm a, khoản 4 điểm a Luật 91/2025. Mỗi dòng truy được về form/model trong code. */}
      <Muc title="2. Dữ liệu chúng tôi thu thập và mục đích">
        <Bang
          head={["Dữ liệu", "Khi nào thu", "Dùng để làm gì"]}
          rows={[
            ["Họ tên, email, số điện thoại, mật khẩu (lưu dạng mã hóa một chiều)", "Khi bạn tạo tài khoản", "Tạo và bảo vệ tài khoản, gửi mã xác thực email, đăng nhập"],
            ["Họ tên, số điện thoại, ghi chú; chi nhánh, ngày giờ, số khách, món đặt trước", "Khi bạn đặt bàn (kể cả không đăng nhập)", "Giữ chỗ, gọi điện xác nhận, chuẩn bị bàn và món"],
            ["Số tiền cọc, mã giao dịch, trạng thái thanh toán", "Khi bạn đặt cọc", "Xác nhận cọc, trừ vào hóa đơn, hoàn cọc theo điều kiện đã công bố"],
            ["Lịch sử xem, yêu thích, gọi và đánh giá món", "Khi bạn dùng website lúc đã đăng nhập", "Gợi ý món theo khẩu vị của bạn (xem mục 3)"],
            ["Câu bạn gõ vào Trợ lý gọi món AI", "Khi bạn dùng trợ lý ở bước gọi món", "Hiểu khẩu vị, số người, ngân sách để đề xuất thực đơn (xem mục 4)"],
            ["Nội dung tin nhắn", "Khi bạn chat với nhân viên", "Trả lời câu hỏi, hỗ trợ đặt bàn"],
            ["Điểm và nhận xét", "Khi bạn đánh giá món hoặc bữa ăn", "Cải thiện món ăn, dịch vụ; nhận xét có thể hiển thị công khai"],
            ["Địa chỉ IP (lưu tạm)", "Khi gửi yêu cầu tới máy chủ", "Chặn đăng ký, đăng nhập, nhập mã liên tục để chống spam và dò mật khẩu"],
          ]}
        />
        <p>Chúng tôi không dùng dữ liệu cho mục đích khác ngoài bảng trên nếu chưa hỏi ý kiến bạn. Chúng tôi không gửi email quảng cáo.</p>
      </Muc>

      {/* Căn cứ: khoản 1 Điều 4 NĐ 356/2025 (điểm l: dữ liệu theo dõi hành vi; sức khỏe); khoản 4 Điều 6 NĐ 356/2025. */}
      <Muc title="3. Dữ liệu nhạy cảm">
        <p>Hai loại dữ liệu dưới đây có thể thuộc nhóm dữ liệu cá nhân nhạy cảm theo Nghị định 356/2025/NĐ-CP:</p>
        <ul>
          <li>
            <strong>Thông tin dị ứng, sức khỏe</strong> bạn tự ghi vào ô ghi chú đặt bàn hoặc gõ cho Trợ lý AI
            (ví dụ "bé dị ứng tôm"). Chúng tôi chỉ dùng để lọc món và phục vụ bữa ăn, không dùng vào việc khác.
            Bạn không bắt buộc phải cung cấp.
          </li>
          <li>
            <strong>Dữ liệu hành vi</strong>: món bạn đã xem, yêu thích, gọi, đánh giá. Chỉ dùng để gợi ý món trên
            website này, không chia sẻ cho bên thứ ba và không dùng cho quảng cáo.
          </li>
        </ul>
        <p>Muốn ngừng gợi ý theo khẩu vị hoặc xóa lịch sử này, gửi yêu cầu theo mục 7.</p>
      </Muc>

      {/* Căn cứ: Điều 11 Luật 134/2025/QH15 (minh bạch AI); checklist 07 mục B. Code: recommendations/tro_ly.py. */}
      <Muc id="tro-ly-ai" title="4. Trợ lý gọi món AI">
        <ul>
          <li>Trợ lý là phần mềm AI, không phải nhân viên. Thực đơn nó đề xuất chỉ để tham khảo.</li>
          <li>
            Câu bạn gõ được gửi tới dịch vụ AI của OpenAI <Dien>xác nhận nhà cung cấp; nếu dùng cổng trung gian qua OPENAI_BASE_URL thì ghi tên cổng đó</Dien> để
            chuyển thành yêu cầu dạng máy hiểu (loại món, khẩu vị, số người, ngân sách, món cần tránh).
            Chỉ câu bạn gõ được gửi đi; họ tên, số điện thoại, email không được gửi kèm.
          </li>
          <li>Chúng tôi yêu cầu nhà cung cấp không lưu nội dung này (tùy chọn <code>store: false</code>).</li>
          <li>Món, giá và khuyến mãi luôn lấy từ thực đơn của nhà hàng, AI không tự đặt ra.</li>
          <li>Không gõ họ tên, số điện thoại hay thông tin không cần thiết vào trợ lý.</li>
          <li>Lọc dị ứng dựa trên thông tin nguyên liệu và có thể sót. Nếu có dị ứng, hãy báo nhân viên khi đến.</li>
          <li>Các nút gợi ý nhanh (Lẩu nướng, Gia đình, Tiết kiệm…) không gửi gì cho AI.</li>
        </ul>
      </Muc>

      {/* Căn cứ: Điều 7 khoản 6 Luật 91/2025 (cấm mua bán dữ liệu); Điều 20 khoản 1 (chuyển xuyên biên giới).
          Code: render.yaml (Render, Singapore), settings.py (Resend, R2), payments/services.py (PayOS chỉ nhận mã đặt bàn + số tiền). */}
      <Muc title="5. Bên nhận dữ liệu và nơi lưu trữ">
        <Bang
          head={["Bên nhận", "Dữ liệu", "Lý do", "Đặt tại"]}
          rows={[
            ["Render (máy chủ ứng dụng, bộ nhớ đệm)", "Toàn bộ dữ liệu ở mục 2 đi qua máy chủ; tin nhắn chat đi qua bộ nhớ đệm", "Vận hành website", "Singapore"],
            [<Dien key="db">nhà cung cấp cơ sở dữ liệu</Dien>, "Dữ liệu ở mục 2", "Lưu trữ", <Dien key="dbr">quốc gia</Dien>],
            ["Resend", "Email, họ tên, mã xác thực", "Gửi email xác thực tài khoản", "Hoa Kỳ"],
            ["OpenAI", "Câu bạn gõ vào Trợ lý AI", "Hiểu yêu cầu gọi món", "Hoa Kỳ"],
            ["PayOS", "Mã đặt bàn, số tiền cọc", "Tạo mã thanh toán cọc", "Việt Nam"],
          ]}
        />
        <p>
          Thông tin tài khoản ngân hàng hoặc thẻ bạn nhập trên trang PayOS và ứng dụng ngân hàng không đi qua website
          của chúng tôi. Chúng tôi không bán dữ liệu cá nhân của bạn.
        </p>
        <p>
          Vì máy chủ và một số dịch vụ đặt ngoài Việt Nam, việc dùng website là có chuyển dữ liệu cá nhân ra nước ngoài.
        </p>
        <p>
          Thời gian lưu: <Dien>ví dụ: dữ liệu tài khoản lưu đến khi bạn yêu cầu xóa; dữ liệu đặt bàn và thanh toán lưu theo thời hạn chứng từ kế toán</Dien>.
          Hết thời hạn, chúng tôi xóa hoặc khử nhận dạng dữ liệu, trừ khi pháp luật yêu cầu lưu lâu hơn.
          Tài khoản đăng ký nhưng chưa xác thực email sẽ bị xóa khi bạn đăng ký lại bằng cùng email.
        </p>
      </Muc>

      {/* Code: api/client.ts (localStorage token), admin/pages/TablesPage.tsx (tùy chọn giao diện). Không có script theo dõi. */}
      <Muc title="6. Cookie và lưu trữ trên trình duyệt">
        <p>
          Website <strong>không dùng</strong> cookie hay công cụ thống kê, quảng cáo (Google Analytics, Facebook Pixel…).
          Trình duyệt chỉ lưu mã đăng nhập để bạn không phải đăng nhập lại; đăng xuất là mã này bị xóa.
        </p>
      </Muc>

      {/* Căn cứ: Điều 4 khoản 1, Điều 10 khoản 2 Luật 91/2025; Điều 5 khoản 2, 3, 4 NĐ 356/2025 (thời hạn). */}
      <Muc id="quyen" title="7. Quyền của bạn">
        <p>Bạn có quyền:</p>
        <ul>
          <li>biết chúng tôi đang xử lý dữ liệu nào của bạn</li>
          <li>đồng ý, không đồng ý, hoặc rút lại sự đồng ý</li>
          <li>xem, chỉnh sửa hoặc yêu cầu chỉnh sửa dữ liệu (họ tên, số điện thoại sửa được ngay tại <Link to="/tai-khoan">trang tài khoản</Link>)</li>
          <li>yêu cầu cung cấp, xóa, hạn chế xử lý dữ liệu, phản đối việc xử lý</li>
          <li>khiếu nại, tố cáo, khởi kiện, yêu cầu bồi thường theo quy định pháp luật</li>
        </ul>
        <p>
          <strong>Cách yêu cầu:</strong> gửi email tới <a href={`mailto:${email}`}>{email}</a> từ email của tài khoản,
          nêu rõ yêu cầu (ví dụ "xóa tài khoản và dữ liệu"). Chúng tôi:
        </p>
        <ul>
          <li>xác nhận đã nhận yêu cầu và hướng dẫn thủ tục trong 2 ngày làm việc</li>
          <li>cho xem, chỉnh sửa, cung cấp dữ liệu trong 10 ngày (15 ngày nếu cần bên xử lý dữ liệu hoặc bên thứ ba cùng thực hiện)</li>
          <li>xử lý yêu cầu rút đồng ý, hạn chế, phản đối trong 15 ngày (20 ngày nếu cần bên xử lý hoặc bên thứ ba ngừng xử lý)</li>
          <li>xóa dữ liệu trong 20 ngày (30 ngày nếu cần bên xử lý hoặc bên thứ ba cùng xóa)</li>
        </ul>
        <p>
          Yêu cầu phức tạp có thể được gia hạn một lần, chúng tôi sẽ báo lý do cho bạn. Khi xóa tài khoản, phiếu đặt bàn
          và chứng từ cọc đã phát sinh vẫn được giữ (không gắn với tài khoản) theo thời hạn lưu chứng từ.
        </p>
      </Muc>

      {/* Căn cứ: Điều 23 khoản 1 Luật 91/2025: báo cơ quan chuyên trách chậm nhất 72 giờ. Báo người dùng là cam kết tự nguyện. */}
      <Muc title="8. Khi có sự cố">
        <p>
          Nếu xảy ra lộ, mất dữ liệu cá nhân, chúng tôi thông báo cho cơ quan chuyên trách bảo vệ dữ liệu cá nhân
          theo quy định. <Dien>có cam kết báo cho người dùng bị ảnh hưởng không? Nếu có, giữ câu: "Chúng tôi cũng báo cho bạn nếu sự cố ảnh hưởng tới dữ liệu của bạn."</Dien>
        </p>
      </Muc>

      <Muc title="9. Thay đổi chính sách">
        <p>
          Khi thay đổi mục đích hoặc loại dữ liệu xử lý, chúng tôi cập nhật trang này, tăng số phiên bản và xin lại sự
          đồng ý khi cần. Xem thêm <Link to="/dieu-khoan">Điều khoản sử dụng</Link>.
        </p>
      </Muc>
    </LegalLayout>
  );
}
