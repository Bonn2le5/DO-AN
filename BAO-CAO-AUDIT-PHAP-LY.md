# Rà soát pháp lý: MỘC Kitchen (web app quản lý nhà hàng)

> 🤖 Báo cáo do AI tạo từ mã nguồn, chỉ để tham khảo, không phải ý kiến pháp lý. Phần lớn mục 🔴 là chỉnh sửa nhỏ trong code, làm được trong vài giờ, không cần quá lo. Việc gì quan trọng thì hỏi lại người làm luật.

**Ngày audit:** 11/11/2026, lần 2. Lần 1 ngày 08/11/2026. Dữ liệu luật của bộ checklist cập nhật 03/11/2026.

**Cập nhật 11/11/2026 sau khi sửa (chưa commit):**
- 🔴 1 → đã có bản nháp `/chinh-sach-bao-mat` và `/dieu-khoan` (`moc-frontend/src/pages/legal/`), footer đã link tới. Còn các ô `[ĐIỀN]` chủ site phải tự điền.
- 🔴 2 → ô nhập trợ lý AI có dòng báo câu gõ được gửi tới dịch vụ AI và dị ứng chỉ dùng để lọc món. Kết quả có dòng "Chỉ để tham khảo, báo nhân viên nếu có dị ứng" (đồng thời xử lý mục 🟡 04-A).
- 🔴 3 → form đăng ký có ô đồng ý không tích sẵn, link tới hai trang. Backend bắt buộc đồng ý và lưu `dong_y_chinh_sach_luc` + `phien_ban_chinh_sach` (migration `accounts/0005`).
- 🔴 4 → bước xác nhận đặt bàn có dòng thông báo mục đích dùng tên, SĐT, ghi chú.
- 🔴 5 → footer và trang Điều khoản đã có chỗ cho tên đơn vị, MST, số ĐKKD, nhưng **vẫn đang là `[ĐIỀN]`**. Mục này chỉ xong khi điền thông tin thật vào `moc-frontend/src/lib/legal.ts`. Trang Điều khoản có mục khiếu nại (🟡 04-D).
- Đính chính: giao diện hồ sơ chỉ thu họ tên và SĐT. Ảnh đại diện, ngày sinh, giới tính có trong model nhưng không có form nào thu, nên Cloudflare R2 hiện chỉ chứa ảnh món. Thanh toán cọc hiện dùng PayOS (Việt Nam) thay VNPay, và chỉ gửi mã đặt bàn cùng số tiền.

**Thay đổi so với lần 1:**
- Đã thêm **trợ lý gọi món AI** (commit `d2be005`). Phần này được audit mới ở mục 07 bên dưới.
- Commit `083411a` sửa nghiệp vụ hoàn cọc theo giờ Việt Nam. Không ảnh hưởng kết luận pháp lý.
- **Cả 4 mục 🔴 của lần 1 vẫn chưa sửa.**

**Kết quả quét:** mức 2, bán hàng/TMĐT.
- Đặt bàn kèm gọi món trước và **đặt cọc online qua VNPay**: `moc-frontend/src/pages/reservation/ContactStep.tsx`, `PaymentStep.tsx`
- Tài khoản người dùng (đăng ký/đăng nhập, xác thực email): `moc-frontend/src/App.tsx`, `pages/auth/RegisterPage.tsx`
- Form thu thập dữ liệu cá nhân: đăng ký (họ tên, email, SĐT), đặt bàn (họ tên, SĐT, ghi chú), hồ sơ (ngày sinh, giới tính, ảnh)
- **Trợ lý gọi món AI:** tin nhắn tự do của khách được gửi tới OpenAI Responses API, hoặc cổng trung gian đặt trong `OPENAI_BASE_URL` (`moc-backend/recommendations/tro_ly.py:196-210`, `pages/reservation/TroLyGoiMon.tsx`). Endpoint mở cho cả khách chưa đăng nhập, giới hạn 20 lượt/phút.
- Gợi ý món TF-IDF ghi lại hành vi từng người: `moc-backend/recommendations/models.py`
- Chat hỗ trợ là nhân viên thật qua WebSocket: `components/chat/ChatWidget.tsx`
- Gửi email qua Resend (nước ngoài): `moc-backend/config/settings.py:213`
- **Đã có cấu hình deploy thật** (`render.yaml`): tên miền `mockitchen.id.vn`, backend và Redis (cache, chat realtime) đặt trên **Render, vùng Singapore**. Ảnh tải lên, kể cả **ảnh đại diện người dùng**, lưu trên **Cloudflare R2** và phát qua `media.mockitchen.id.vn` (`settings.py:245-258`). Database lấy từ `DATABASE_URL`, nhà cung cấp chưa xác định từ code. Cấu hình có thêm cổng thanh toán payOS bên cạnh VNPay.

Vài tín hiệu TRACKING, PERMISSIONS, FOREIGN_HOST của script là bắt nhầm từ thư viện trong `.venv`. Frontend không có Google Analytics, Pixel hay script theo dõi nào.

**Phạm vi rà soát:** 01 Bảo vệ dữ liệu cá nhân, 02 Thương mại điện tử, 04 Bảo vệ người tiêu dùng, 06 Giao dịch điện tử, 07 Minh bạch AI.

> **Bối cảnh đồ án:** đây là đồ án, nhưng `render.yaml` cho thấy site được triển khai công khai tại `mockitchen.id.vn`. Nếu người thật đăng ký tài khoản hay đặt bàn trên bản deploy này, dữ liệu của họ đã được xử lý thật. Báo cáo đánh giá theo giả định **site đang vận hành thật**. Lần audit 08/11 ghi "chạy localhost, chưa deploy" là chưa chính xác.

## Tổng quan

| Lĩnh vực | 🔴 | 🟡 | 🟢 |
|---|---|---|---|
| Bảo vệ dữ liệu cá nhân | 4 | 3 | 1 |
| Thương mại điện tử | 1 | 1 | 1 |
| Bảo vệ người tiêu dùng | 0 | 2 | 3 |
| Giao dịch điện tử | 0 | 0 | 2 |
| Minh bạch AI | 0 | 1 | 3 |

**Không áp dụng:** Quảng cáo (không có KOL, affiliate hay quảng cáo theo hành vi). Mobile app (không có). An ninh mạng/lưu trữ dữ liệu trong nước (checklist 03) không được rà chi tiết: nghĩa vụ lưu trữ trong nước chủ yếu nhắm tới doanh nghiệp cung cấp dịch vụ viễn thông/Internet quy mô lớn. Mức phạt và đối tượng cụ thể: CHƯA XÁC MINH, nên hỏi người làm luật nếu vận hành thương mại.

## 🔴 Cần xử lý ngay

1. **01-A / 02-C. Không có trang chính sách bảo vệ dữ liệu cá nhân và điều khoản sử dụng** *(chưa sửa từ lần 1)*. Footer chỉ in chữ "Điều khoản · Chính sách bảo mật" dạng `<span>` (`components/layout/Footer.tsx:85`). `App.tsx` không có route cho hai trang này.
   - Căn cứ: Luật BVDLCN 91/2025/QH15; NĐ 356/2025/NĐ-CP; Luật TMĐT 122/2025/QH15 Điều 11.
   - Đề xuất: tạo `/chinh-sach-bao-mat` và `/dieu-khoan`, đổi footer thành `<Link>`. Chính sách nêu: loại dữ liệu, mục đích, thời gian lưu, **bên nhận và nơi lưu (Render Singapore, Cloudflare R2, VNPay/payOS, Resend, nhà cung cấp AI)**, quyền của khách, kênh liên hệ.

2. **01-B / 07-B. Trợ lý AI gửi tin nhắn của khách tới dịch vụ AI bên ngoài mà không báo cho khách** *(mới)*. Ô nhập (`TroLyGoiMon.tsx:159`) không có dòng nào nói tin nhắn được gửi đi đâu. Prompt hệ thống còn chủ động mời khách khai **dị ứng** ("bé dị ứng tôm" → `di_ung_tom`). Dị ứng là thông tin sức khỏe, thuộc nhóm **dữ liệu nhạy cảm**.
   - Căn cứ: Điều 9 Luật 91/2025 (đồng ý rõ ràng, theo mục đích); khoản 4 Điều 6 NĐ 356/2025 (phải báo khi xử lý dữ liệu nhạy cảm); checklist 07 mục B (tin nhắn chatbot gửi bên thứ ba thì xét 01-B và 01-D).
   - Đề xuất: thêm một dòng nhỏ dưới ô nhập: "Yêu cầu của bạn được gửi tới dịch vụ AI để hiểu khẩu vị. Không nhập họ tên, số điện thoại. Thông tin dị ứng chỉ dùng để lọc món. [Chính sách bảo mật]". Các nút gợi ý nhanh không gọi AI nên không cần thông báo này. Điểm cộng đã có: `"store": False` (`tro_ly.py:205`) và chỉ gửi đúng câu khách gõ, không kèm tên, SĐT hay lịch sử. Nên ghi rõ cả hai điểm này trong chính sách.

3. **01-B. Form đăng ký tài khoản không thông báo mục đích, không xin đồng ý** *(chưa sửa)*. Xem `pages/auth/RegisterPage.tsx`. Không có ô đồng ý và không có link chính sách. Câu "Nhận ưu đãi và gợi ý món ăn dành riêng cho bạn" gộp ngầm mục đích tiếp thị.
   - Căn cứ: Điều 9 Luật 91/2025 (khoản 4 điểm b: không gộp mục đích); khoản 3 Điều 6 NĐ 356/2025 (không tích sẵn).
   - Đề xuất: thêm ô bắt buộc "Tôi đồng ý với Điều khoản và Chính sách bảo mật" (không tích sẵn), một ô tùy chọn riêng cho email ưu đãi, và lưu thời điểm cùng phiên bản chính sách khách đã đồng ý ở backend.

4. **01-B. Form đặt bàn thu họ tên, SĐT mà không có thông báo xử lý dữ liệu** *(chưa sửa)*. Xem `pages/reservation/ContactStep.tsx:11-15`.
   - Căn cứ: Điều 9 Luật 91/2025; NĐ 356/2025.
   - Đề xuất: thêm một dòng trên nút xác nhận: "Nhà hàng dùng tên và số điện thoại để xác nhận đặt chỗ. Xem [Chính sách bảo mật]".

5. **02-C. Thiếu thông tin chủ sở hữu bắt buộc** *(chưa sửa)*. Không có tên đơn vị, mã số thuế, số ĐKKD, cũng chưa có cơ chế khiếu nại.
   - Căn cứ: Luật TMĐT 122/2025/QH15 Điều 11, Điều 15; NĐ 248/2026/NĐ-CP Điều 4 (theo nguồn thứ cấp).
   - Đề xuất: bổ sung vào footer. Đồ án có thể ghi dữ liệu mẫu và chú thích "dự án học tập".

## 🟡 Nên cải thiện

- **01-A. Chưa có chức năng xóa tài khoản / yêu cầu xóa dữ liệu** *(chưa sửa)*. Căn cứ: Luật 91/2025; khoản 4 Điều 5 NĐ 356/2025 (20 ngày). Đề xuất: nút "Xóa tài khoản" trong `/tai-khoan`, hoặc ghi email nhận yêu cầu xóa trong chính sách.
- **01-A/C. Dữ liệu hành vi cho gợi ý món** (`TuongTacMonAn`). Trợ lý AI cũng dùng dữ liệu này (`_mon_khach_tung_goi`, `tro_ly.py:324`). NĐ 356/2025 xếp "dữ liệu theo dõi hành vi trên không gian mạng" vào nhóm nhạy cảm (điểm l khoản 1 Điều 4). Chưa có hướng dẫn trường hợp này có thuộc nhóm đó không. **Nên hỏi người làm luật.** Cách an toàn là nêu trong chính sách và cho khách tắt gợi ý cá nhân hóa.
- **01-B. Rút lại đồng ý nhận email ưu đãi** khi đã có ô đồng ý (Điều 10 khoản 2 Luật 91/2025).
- **02-B. Thông báo nền tảng bán hàng trực tiếp với Bộ Công Thương** (Điều 14 Luật 122/2025). Chỉ cần khi vận hành thật. Nên hỏi người làm luật.
- **04-A. Lọc dị ứng của trợ lý AI dựa trên từ khóa** trong tên, mô tả, nguyên liệu (`TU_THANH_PHAN`, `tro_ly.py`). Nếu món nào ghi thiếu nguyên liệu, AI có thể gợi ý nhầm món khách dị ứng. Luật 19/2023/QH15 (Điều 21) yêu cầu thông tin sản phẩm trung thực, đầy đủ. Đề xuất: khi khách có nhắc dị ứng, hiện thêm một dòng "Vui lòng báo nhân viên về dị ứng khi đến, thực đơn AI chỉ để tham khảo".
- **04-D. Kênh khiếu nại.** Chưa công bố. Luật yêu cầu báo đã tiếp nhận trong 03 ngày làm việc (Điều 31 khoản 2 Luật 19/2023).
- **07-D. Phân loại rủi ro và nhà cung cấp.** Trợ lý AI ở mức rủi ro **thấp**: chỉ đọc ý định, món do database chọn, có nhãn AI rõ ràng (Điều 9 Luật 134/2025). Site là **bên triển khai** của mô hình OpenAI, đồng thời là **nhà cung cấp** của hệ thống trợ lý tự xây. Không có nghĩa vụ đánh giá bắt buộc, nhưng nên ghi một đoạn ngắn trong chính sách về cách trợ lý hoạt động.

**Giấy tờ, thủ tục (chỉ khi vận hành thật, nên hỏi người làm luật):**
- **Chuyển dữ liệu xuyên biên giới, đã phát sinh thật nếu bản deploy có người dùng.** Toàn bộ backend và Redis chạy trên Render ở **Singapore**, ảnh đại diện lưu trên Cloudflare R2, tin nhắn trợ lý AI gửi tới OpenAI (Mỹ), email gửi qua Resend (Mỹ). Theo Điều 20 Luật 91/2025, "lưu trữ đặt ở nước ngoài" hoặc "dùng nền tảng ở nước ngoài để xử lý" đều tính là chuyển xuyên biên giới. Trường hợp này thuộc diện lập hồ sơ đánh giá tác động trong 60 ngày kể từ lần chuyển đầu tiên (khoản 2 Điều 20). Hộ kinh doanh và doanh nghiệp siêu nhỏ **không** được miễn. Khoản 6 Điều 20 chỉ miễn khi lưu dữ liệu **người lao động**, không miễn cho dữ liệu khách hàng. Với đồ án học tập, cách đơn giản nhất là ghi rõ trên site "bản demo, không nhập dữ liệu thật" và dùng dữ liệu mẫu. Nên hỏi người làm luật nếu vận hành thương mại.
- Hồ sơ đánh giá tác động xử lý dữ liệu (Điều 21) và nhân sự bảo vệ dữ liệu (khoản 2 Điều 33): được miễn nếu là hộ kinh doanh hoặc doanh nghiệp siêu nhỏ (khoản 3 Điều 38). Ngoại lệ là khi bị coi là **trực tiếp xử lý dữ liệu nhạy cảm**: thông tin dị ứng qua trợ lý AI và dữ liệu hành vi có thể khiến site mất miễn trừ. Cần hỏi người làm luật.
- Quy trình báo cáo sự cố rò rỉ dữ liệu trong 72 giờ (Điều 23 Luật 91/2025).

## 🟢 Đạt yêu cầu

- **07-B. Trợ lý AI được gắn nhãn rõ ràng:** "Trợ lý gọi món AI", huy hiệu "AI Mộc", "Thực đơn AI đề xuất", "AI Mộc đang lên thực đơn…" (`TroLyGoiMon.tsx:139-211`). Không đóng giả nhân viên thật (Điều 11 khoản 1 Luật 134/2025).
- **07-C. AI không tạo tên món, giá hay khuyến mãi.** Prompt cấm AI nêu tên món hay giá, toàn bộ lấy từ database. Không phát sinh nội dung AI dễ gây nhầm về tính xác thực.
- **07/01. Tối thiểu hóa dữ liệu gửi AI:** chỉ gửi câu khách gõ, `store: False`, có rate limit 20/phút, AI lỗi thì trả 503 thay vì đoán bừa.
- **01-C. Không có tracking hay cookie quảng cáo**, nên không cần banner cookie.
- **02-H / 04-A. Giá và tiền cọc minh bạch** trước khi bấm đặt.
- **04-B. Có bước xác nhận rõ ràng** và thời hạn giữ chỗ.
- **04-D. Điều kiện hoàn cọc công bố ngay tại bước đặt.** Mốc hoàn cọc nay tính theo giờ Việt Nam (commit `083411a`).
- **06-A. Lưu bản ghi giao dịch** (đặt bàn, thanh toán, mã VNPay, thời điểm).
- **Không lưu số thẻ:** thanh toán qua cổng VNPay.

## Ngoài phạm vi, nên kiểm tra riêng

- JWT lưu trong `localStorage` (`api/client.ts`) dễ bị lộ nếu dính lỗi XSS.
- Endpoint trợ lý AI cho phép khách chưa đăng nhập gọi (`AllowAny`). Đã có giới hạn 20 lượt/phút; nên theo dõi chi phí API.
- Ảnh đại diện người dùng nằm trên tên miền công khai `media.mockitchen.id.vn`. Ai có URL là xem được. Nên đặt tên file khó đoán, hoặc tách bucket riêng cho ảnh người dùng.

## Mức phạt tham khảo

Chỉ nêu cho các mục 🔴 về đồng ý và thông tin xử lý dữ liệu. Theo NĐ 330/2026/NĐ-CP Điều 43 khoản 1, hành vi "xử lý dữ liệu khi chưa có đồng ý; xin đồng ý không rõ ràng, không theo từng mục đích; không cung cấp đủ thông tin; không báo khi xử lý dữ liệu nhạy cảm; không lưu bằng chứng đồng ý" có **mức tối đa theo quy định tham khảo được** là 30-50 triệu đồng với tổ chức, và 15-25 triệu đồng với cá nhân hoặc hộ kinh doanh. Có thể bị buộc xóa dữ liệu thu trái phép (Điều 5 NĐ 330/2026).

Mục 🔴 về thông tin chủ sở hữu (Luật TMĐT): mức phạt CHƯA XÁC MINH. Chưa có nghị định xử phạt riêng về AI.

## Bước tiếp theo

Bốn trong năm mục 🔴 có cùng gốc là **chưa có trang chính sách bảo mật**. Bạn có thể yêu cầu "**soạn chính sách bảo mật cho dự án này**": AI sẽ soạn chính sách (có phần về trợ lý AI và dữ liệu dị ứng) cùng các dòng thông báo/ô đồng ý cho form đăng ký, form đặt bàn và ô nhập trợ lý AI.

## Giới hạn & khuyến nghị

> Báo cáo này do AI tạo dựa trên bộ checklist tổng hợp từ văn bản pháp luật công khai, **không phải ý kiến tư vấn pháp lý chính thức**. Khung pháp lý Việt Nam về dữ liệu cá nhân, TMĐT, an ninh mạng và AI vừa thay đổi lớn trong 2025-2026. Trước khi quyết định, hãy xác minh lại từng văn bản tại thuvienphapluat.vn/vbpl.vn và tham vấn luật sư.
>
> Rà soát dựa trên mã nguồn, chưa chạy site trên trình duyệt. Các phần chưa kiểm tra: nội dung trang khuyến mãi và bài viết, email mẫu gửi khách, chức năng xuất Excel dữ liệu khách ở trang admin, tính năng đánh giá bữa ăn mới thêm (`DanhGiaBuaAn`).
