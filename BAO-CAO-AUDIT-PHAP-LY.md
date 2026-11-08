# Rà soát pháp lý: MỘC Kitchen (web app quản lý nhà hàng)

> 🤖 Báo cáo do AI tạo từ mã nguồn, chỉ để tham khảo, không phải ý kiến pháp lý. Phần lớn mục 🔴 là chỉnh sửa nhỏ trong code, làm được trong vài giờ, không cần quá lo. Việc gì quan trọng thì hỏi lại người làm luật.

**Ngày audit:** 08/11/2026 (dữ liệu luật của bộ checklist cập nhật 03/11/2026)
**Kết quả quét:** mức 2, bán hàng/TMĐT.
- Đặt bàn kèm gọi món trước và **đặt cọc online qua VNPay**: `moc-frontend/src/pages/reservation/ContactStep.tsx`, `PaymentStep.tsx`, `moc-backend/config/settings.py:265`
- Tài khoản người dùng (đăng ký/đăng nhập, xác thực email): `moc-frontend/src/App.tsx:13-14`, `pages/auth/RegisterPage.tsx`
- Form thu thập dữ liệu cá nhân: đăng ký (họ tên, email, SĐT, mật khẩu), đặt bàn (họ tên, SĐT, ghi chú), hồ sơ tài khoản (thêm ngày sinh, giới tính, ảnh đại diện: `moc-backend/accounts/models.py:103-114`)
- Hệ thống gợi ý món "AI" tự xây (TF-IDF + cosine), ghi lại hành vi xem/yêu thích/đặt món của từng người dùng: `moc-backend/recommendations/models.py:6`, `pages/reservation/FoodSuggestions.tsx:12`
- Chat hỗ trợ khách là **nhân viên thật** qua WebSocket, không phải chatbot AI: `components/chat/ChatWidget.tsx`
- Gửi email qua Resend, dịch vụ đặt ở nước ngoài: `moc-backend/config/settings.py:200`

Vài tín hiệu của script quét là **bắt nhầm** từ thư viện trong `.venv`: TRACKING (`twisted`), PERMISSIONS, FOREIGN_HOST (`kombu/SQS`). Frontend **không có** Google Analytics, Facebook Pixel hay script theo dõi nào. `localStorage` chỉ dùng để lưu token đăng nhập và tùy chọn giao diện admin.

**Phạm vi rà soát:** 01 Bảo vệ dữ liệu cá nhân, 02 Thương mại điện tử, 04 Bảo vệ người tiêu dùng, 06 Giao dịch điện tử, 07 Minh bạch AI (cho hệ gợi ý món).

> **Bối cảnh đồ án:** hiện đây là dự án học tập chạy ở localhost với VNPay sandbox, nên chưa phát sinh nghĩa vụ thực tế. Báo cáo đánh giá theo giả định **site được đưa vào vận hành thật**. Các mục 🔴 vẫn nên sửa để sản phẩm đúng chuẩn khi bảo vệ đồ án.

## Tổng quan

| Lĩnh vực | 🔴 | 🟡 | 🟢 |
|---|---|---|---|
| Bảo vệ dữ liệu cá nhân | 3 | 3 | 1 |
| Thương mại điện tử | 1 | 1 | 1 |
| Bảo vệ người tiêu dùng | 0 | 1 | 3 |
| Giao dịch điện tử | 0 | 0 | 2 |
| Minh bạch AI | 0 | 1 | 1 |

**Không áp dụng:** Quảng cáo (không có KOL, affiliate hay quảng cáo theo hành vi; form "Nhận ưu đãi" ở footer chưa gửi dữ liệu đi đâu). An ninh mạng/lưu trữ dữ liệu trong nước (chưa deploy; xem lại khi chọn hosting). Mobile app (không có).

## 🔴 Cần xử lý ngay

1. **01-A / 02-C. Không có trang chính sách bảo vệ dữ liệu cá nhân và điều khoản sử dụng.** Footer chỉ in chữ "Điều khoản · Chính sách bảo mật" dạng `<span>`, không link tới trang nào (`components/layout/Footer.tsx:84`), và `App.tsx` không có route cho hai trang này.
   - Căn cứ: Luật BVDLCN 91/2025/QH15 (Điều 4 khoản 1 về quyền chủ thể dữ liệu); NĐ 356/2025/NĐ-CP; Luật TMĐT 122/2025/QH15 Điều 11 (công bố quy chế hoạt động, chính sách bảo vệ dữ liệu cá nhân).
   - Đề xuất: tạo route `/chinh-sach-bao-mat` và `/dieu-khoan`, đổi chữ ở footer thành `<Link>`. Chính sách cần nêu: loại dữ liệu thu (họ tên, email, SĐT, ngày sinh, giới tính, ảnh, lịch sử đặt bàn/đặt món, hành vi xem món), mục đích, thời gian lưu, bên nhận (VNPay, Resend), quyền của khách, email liên hệ và thời hạn xử lý theo Điều 5 NĐ 356/2025.

2. **01-B. Form đăng ký tài khoản không có thông báo mục đích và không xin đồng ý.** Form thu họ tên, email, SĐT (`pages/auth/RegisterPage.tsx:44`) nhưng không có ô đồng ý, không link chính sách. Câu "Nhận ưu đãi và gợi ý món ăn dành riêng cho bạn" (dòng 39) còn ngầm gộp mục đích tiếp thị và cá nhân hóa vào việc tạo tài khoản.
   - Căn cứ: Điều 9 Luật 91/2025 (đồng ý tự nguyện, rõ ràng, theo từng mục đích; khoản 4 điểm b: không gộp mục đích khác); khoản 3 Điều 6 NĐ 356/2025 (không tích sẵn).
   - Đề xuất: thêm ô "Tôi đồng ý với Điều khoản và Chính sách bảo mật" (bắt buộc, **không tích sẵn**). Tách một ô **tùy chọn** riêng cho "Nhận email ưu đãi". Ở backend, lưu thời điểm và phiên bản chính sách đã đồng ý, ví dụ trường `dong_y_chinh_sach_luc`, `phien_ban_chinh_sach` trong `NguoiDung`, để chứng minh được (khoản 1, 2 Điều 6 NĐ 356/2025).

3. **01-B. Form đặt bàn thu họ tên, SĐT (cả khách chưa đăng nhập) mà không có thông báo xử lý dữ liệu.** Xem `pages/reservation/ContactStep.tsx:11-15`; dữ liệu lưu vào `DatBan.ten_khach`, `sdt_khach` (`reservations/models.py:203-205`).
   - Căn cứ: Điều 9 Luật 91/2025; NĐ 356/2025.
   - Đề xuất: đặt bàn là việc cần SĐT để thực hiện hợp đồng, nên không nhất thiết phải có ô tích. Tối thiểu thêm một dòng ngay trên nút "Xác nhận đặt chỗ": "Nhà hàng dùng tên và số điện thoại để xác nhận đặt chỗ. Xem [Chính sách bảo mật]". Ô ghi chú có thể chứa thông tin sức khỏe như dị ứng hay có trẻ em, nên chính sách nên nhắc đến.

4. **02-C. Thiếu thông tin chủ sở hữu bắt buộc.** Footer có địa chỉ, email, SĐT, nhưng không có tên pháp nhân hoặc chủ hộ kinh doanh, mã số thuế, số giấy chứng nhận đăng ký kinh doanh. Cũng chưa có cơ chế khiếu nại, tranh chấp.
   - Căn cứ: Luật TMĐT 122/2025/QH15 Điều 11, Điều 15; NĐ 248/2026/NĐ-CP Điều 4 (theo nguồn thứ cấp).
   - Đề xuất: bổ sung vào footer tên đơn vị, MST, số ĐKKD. Đồ án có thể ghi dữ liệu mẫu và chú thích "dự án học tập".

## 🟡 Nên cải thiện

- **01-A. Chưa có chức năng xóa tài khoản / yêu cầu xóa dữ liệu.** Không tìm thấy endpoint hay giao diện nào trong `accounts/`, `api/`. Hồ sơ tài khoản đã cho xem và sửa thông tin (🟢). Căn cứ: Luật 91/2025 (quyền xóa); khoản 4 Điều 5 NĐ 356/2025 (thời hạn 20 ngày). Đề xuất: thêm nút "Xóa tài khoản" trong `/tai-khoan`, hoặc tối thiểu ghi trong chính sách một email nhận yêu cầu xóa. Khi xóa, dùng `on_delete=SET_NULL` như `DatBan.nguoi_dung` để vẫn giữ được chứng từ cọc.
- **01-A/C. Dữ liệu hành vi dùng cho gợi ý món.** `TuongTacMonAn` ghi lại việc xem, yêu thích, đặt, đánh giá món của từng người để cá nhân hóa. NĐ 356/2025 xếp "dữ liệu theo dõi hành vi... trên không gian mạng" vào nhóm **nhạy cảm** (điểm l khoản 1 Điều 4). Chưa có hướng dẫn hệ gợi ý trong nội bộ một nhà hàng có thuộc nhóm này hay không. **Nên hỏi người làm luật.** Cách an toàn: nêu rõ trong chính sách, và cho người dùng tắt "gợi ý theo khẩu vị" (khi tắt thì hiện "Món được gọi nhiều", đúng như cách code đang xử lý khách mới).
- **01-B. Rút lại đồng ý.** Khi đã thêm ô nhận email ưu đãi, cần chỗ để tắt lại, ví dụ một công tắc trong hồ sơ hoặc link hủy đăng ký trong email (Điều 10 khoản 2 Luật 91/2025).
- **02-B. Thông báo nền tảng TMĐT với Bộ Công Thương.** Site tự bán dịch vụ của mình và có chức năng đặt hàng, đặt cọc, nên thuộc "nền tảng bán hàng trực tiếp" (Điều 3 Luật 122/2025) và phải **thông báo** (Điều 14). Đây là thủ tục, chỉ cần khi vận hành thật. Nên hỏi người làm luật.
- **04-D. Kênh khiếu nại.** Chưa công bố cách khiếu nại và thời hạn phản hồi. Luật yêu cầu báo đã tiếp nhận trong 03 ngày làm việc (Điều 31 khoản 2 Luật 19/2023/QH15). Đề xuất: thêm một mục trong trang điều khoản, kèm email/SĐT.
- **07. Minh bạch AI cho hệ gợi ý món.** Đây là hệ thống AI do chính site phát triển, nên site là **nhà cung cấp** theo Luật 134/2025/QH15. Hệ thống không tạo nội dung giả và không đóng giả người, nên rủi ro thấp. Nên ghi một dòng trong chính sách giải thích gợi ý dựa trên gì, và giữ nhãn "Gợi ý theo khẩu vị của bạn" như hiện tại.

**Giấy tờ, thủ tục (chỉ khi vận hành thật, nên hỏi người làm luật):**
- Email gửi qua **Resend** (máy chủ ở nước ngoài) có kèm email và tên khách. Về lý thuyết, việc này thuộc diện lập hồ sơ đánh giá tác động chuyển dữ liệu xuyên biên giới trong 60 ngày (khoản 2 Điều 20 Luật 91/2025). Hộ kinh doanh và doanh nghiệp siêu nhỏ **không** được miễn nghĩa vụ này. Nếu sau này dùng hosting hoặc database ở nước ngoài (Vercel, AWS, Render…), hoặc gọi API AI nước ngoài cho chatbot, cũng áp dụng tương tự.
- Hồ sơ đánh giá tác động xử lý dữ liệu (Điều 21) và nhân sự bảo vệ dữ liệu (khoản 2 Điều 33) được miễn nếu là hộ kinh doanh hoặc doanh nghiệp siêu nhỏ (khoản 3 Điều 38 Luật 91/2025). Ngoại lệ là khi bị coi là trực tiếp xử lý dữ liệu nhạy cảm (xem mục dữ liệu hành vi ở trên).
- Quy trình báo cáo sự cố rò rỉ dữ liệu trong 72 giờ (Điều 23 Luật 91/2025).

## 🟢 Đạt yêu cầu

- **01-C. Không có tracking hay cookie quảng cáo**, nên không cần banner cookie. `localStorage` chỉ chứa token đăng nhập, là thành phần thiết yếu.
- **02-H / 04-A. Giá và tiền cọc minh bạch:** hiển thị tổng tiền món, % cọc và số tiền cọc trước khi bấm, kèm ghi chú "trừ vào hóa đơn" (`ContactStep.tsx`).
- **04-B. Có bước xác nhận rõ ràng** trước khi thanh toán ("Đặt chỗ và cọc …"), và nêu thời hạn giữ chỗ ("Bạn có N phút để thanh toán").
- **04-D. Điều kiện hoàn cọc được công bố ngay tại bước đặt** ("Xem điều kiện hoàn cọc", theo mốc thời gian hủy).
- **06-A. Giao dịch điện tử:** có đề nghị và chấp thuận rõ ràng. Backend lưu bản ghi đặt bàn, thanh toán, mã giao dịch VNPay và thời điểm (`payments/models.py`), dùng làm chứng cứ được.
- **07-B. Chat hỗ trợ là nhân viên thật**, nên không phát sinh nghĩa vụ thông báo "đang chat với AI".
- **Không thu thông tin thẻ:** thanh toán chuyển sang cổng VNPay, site không lưu số thẻ.

## Lưu ý cho tính năng sắp làm: AI hỗ trợ đặt món (chatbot)

Khi thêm chatbot AI gọi API LLM (Claude, OpenAI…), cần:
- Ghi rõ "Trợ lý AI" ở đầu khung chat. Không đặt tên hay ảnh khiến khách tưởng là nhân viên thật (Điều 11 khoản 1 Luật 134/2025). Không nên đặt persona kiểu "chị Lan, nhân viên tư vấn".
- Tách rõ chatbot AI với chat nhân viên hiện có. Cho khách chuyển sang nhân viên thật.
- Trong chính sách, nêu rằng tin nhắn được gửi tới nhà cung cấp AI ở nước ngoài (liên quan mục D, chuyển dữ liệu xuyên biên giới). Hạn chế gửi SĐT/email của khách vào prompt.
- Thời hạn: hệ thống AI đưa vào sau 01/03/2026 áp dụng luật ngay (Điều 35 Luật 134/2025).

## Ngoài phạm vi, nên kiểm tra riêng

- JWT lưu trong `localStorage` (`api/client.ts`) dễ bị lộ nếu site dính lỗi XSS. Đây là vấn đề bảo mật code, không thuộc checklist pháp lý.

## Mức phạt tham khảo

Chỉ nêu cho các mục 🔴 về đồng ý và thông tin xử lý dữ liệu. Theo NĐ 330/2026/NĐ-CP Điều 43 khoản 1, hành vi "xử lý dữ liệu khi chưa có đồng ý; xin đồng ý không rõ ràng, không theo từng mục đích; không cung cấp đủ thông tin; không lưu bằng chứng đồng ý" có **mức tối đa theo quy định tham khảo được** là 30-50 triệu đồng với tổ chức, và 15-25 triệu đồng với cá nhân hoặc hộ kinh doanh. Ngoài tiền phạt, có thể bị buộc xóa dữ liệu đã thu trái phép (Điều 5 NĐ 330/2026).

Mục 🔴 về thông tin chủ sở hữu (Luật TMĐT): mức phạt CHƯA XÁC MINH.

## Bước tiếp theo

Site đang thu dữ liệu nhưng chưa có chính sách. Bạn có thể yêu cầu "**soạn chính sách bảo mật cho dự án này**": AI sẽ soạn bản nháp chính sách và form đồng ý, dựa trên đúng các trường dữ liệu mà code đang thu.

## Giới hạn & khuyến nghị

> Báo cáo này do AI tạo dựa trên bộ checklist tổng hợp từ văn bản pháp luật công khai, **không phải ý kiến tư vấn pháp lý chính thức**. Khung pháp lý Việt Nam về dữ liệu cá nhân, TMĐT và an ninh mạng vừa thay đổi lớn trong 2025-2026. Trước khi quyết định, hãy xác minh lại từng văn bản tại thuvienphapluat.vn/vbpl.vn và tham vấn luật sư.
>
> Rà soát dựa trên mã nguồn, chưa chạy site trên trình duyệt. Các phần chưa kiểm tra: nội dung trang khuyến mãi và bài viết (quảng cáo), email mẫu gửi khách, giao diện admin xuất dữ liệu khách (Excel qua `openpyxl`).
