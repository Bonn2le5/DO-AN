---
name: backend-completion-plan
description: "Đọc một frontend đang dùng mock data và lập phương án hoàn thiện backend production-ready. Dùng khi cần phân tích API contract, database schema, auth JWT, đơn hàng, đặt bàn, Redis hold, thanh toán VNPay, realtime chat, admin, testing và kế hoạch thay mock bằng API thật."
argument-hint: "Mô tả backend muốn hoàn thiện, stack hoặc ràng buộc nếu có"
user-invocable: true
disable-model-invocation: false
---

# Lập Phương Án Hoàn Thiện Backend

## Mục tiêu

Biến một frontend chưa kết nối backend thành một bản đặc tả triển khai có thể giao cho team backend. Skill này chỉ phân tích và lập phương án, không tự tạo backend trừ khi người dùng yêu cầu thêm.

Đầu ra phải trả lời được:

- Frontend đang cần những resource, endpoint, request, response và lỗi nào.
- Mô hình dữ liệu, quan hệ, trạng thái và ràng buộc nghiệp vụ cần có.
- Thành phần hạ tầng nào cần dùng: database, cache/lock, queue, storage, payment gateway, email hoặc realtime.
- Thứ tự triển khai nhỏ nhất để frontend có thể chuyển từ mock sang API thật an toàn.
- Tiêu chí kiểm thử, bảo mật, vận hành và nghiệm thu.

## Khi sử dụng

Dùng skill khi người dùng nói các ý như:

- “frontend chưa nối backend”, “đọc codebase và đề xuất backend”.
- “thay mock bằng API thật”, “thiết kế Django API cho project”.
- “lập database/API plan cho app đặt món, đặt bàn, thanh toán”.
- “backend còn TODO trong lớp api”, “cần đặc tả backend trước khi code”.

Nếu người dùng đã cung cấp backend hiện có, đọc cả backend và đối chiếu contract thay vì mặc định thiết kế mới.

## Quy trình

### 1. Xác định phạm vi và bằng chứng

1. Đọc `README.md`, `package.json`, cấu hình môi trường, router và entry point.
2. Tìm các file API, `TODO(backend)`, `mockDelay`, mock data, type dùng chung, store và form submit.
3. Đọc mỗi module API cùng call site quan trọng để biết endpoint được dùng như thế nào, không suy đoán chỉ từ tên file.
4. Ghi lại stack frontend, giả định backend hiện có, database hoặc dịch vụ đã được chỉ định.
5. Phân biệt rõ ba mức:
   - **Đã xác định**: có trong type, payload, comment, UI hoặc README.
   - **Suy luận hợp lý**: cần cho nghiệp vụ nhưng chưa có bằng chứng trực tiếp.
   - **Chưa quyết định**: cần hỏi người dùng hoặc đánh dấu lựa chọn.

Điểm kết thúc bước này là một bảng inventory có file nguồn, chức năng, endpoint dự kiến, auth requirement và rủi ro.

### 2. Trích xuất API contract từ frontend

Với từng resource, ghi:

- Method và path chuẩn hóa, ví dụ `/api/auth/login/`.
- Query, path params, request body và field bắt buộc.
- Response shape tương ứng với TypeScript type.
- Pagination, filtering, sorting, search và empty state.
- HTTP status cho success và lỗi validation, unauthorized, forbidden, conflict, not found, expired hoặc payment failure.
- Dữ liệu nào frontend hiện đang tính nhưng backend phải tính lại, đặc biệt giá, discount, subtotal, deposit và stock.

Tối thiểu kiểm tra các nhóm nếu chúng xuất hiện trong repo:

- Auth và user profile.
- Categories, foods, combos, reviews, recommendations.
- Promotions và validate/apply promo code.
- Orders, order items, payment và lịch sử đơn.
- Branches, tables, availability và reservation.
- Table hold có TTL, race condition và release.
- VNPay callback/return URL và idempotency.
- Blog/posts.
- Chat/WebSocket hoặc notification.
- Upload ảnh và admin content management.

Không coi object frontend lồng đầy đủ như `CartItem.food` là schema request bắt buộc. Ưu tiên gửi ID, quantity và note; server phải đọc giá và trạng thái món từ database.

### 3. Thiết kế domain và database

Đề xuất entity, trường chính, foreign key, index, unique constraint, soft delete hoặc audit field khi cần. Bao gồm tối thiểu:

- User, role và profile.
- Branch, table và khu vực.
- Category, food, combo và food availability/stock.
- Promotion, điều kiện áp dụng và usage limit.
- Order, order item, order status history và payment.
- Reservation, reservation food item, table hold và cancellation policy.
- Review và recommendation event hoặc preference nếu có AI.
- Blog post và media nếu frontend dùng CMS.

Với mọi trạng thái, lập state transition hợp lệ và actor được phép chuyển trạng thái. Tách trạng thái nghiệp vụ khỏi trạng thái thanh toán. Dùng decimal/integer phù hợp cho tiền, lưu timezone rõ ràng và không tin giá do client gửi.

Đối với đặt bàn, mô tả invariant: một table không được có hai reservation hợp lệ trùng khoảng thời gian; hold phải hết hạn; confirm phải kiểm tra hold atomically; payment callback không được tạo confirm trùng.

### 4. Chọn kiến trúc triển khai

Nếu repo đã ghi Django/Django REST Framework, giữ lựa chọn đó và đề xuất app/module tương ứng. Nếu chưa có quyết định, đưa ra một lựa chọn mặc định và tối đa một phương án thay thế, kèm lý do ngắn.

Nêu rõ:

- API layer, serializer/schema, service/use-case layer và repository/model boundary.
- PostgreSQL cho dữ liệu giao dịch.
- Redis cho cache, distributed lock và table hold TTL khi flow yêu cầu.
- Celery/RQ hoặc cơ chế queue cho email, payment reconciliation, recommendation refresh nếu cần.
- Django Channels/WebSocket chỉ khi chat/realtime thực sự có call site.
- Object storage cho ảnh nếu placeholder sẽ thay bằng media thật.
- Docker, environment variables, CORS, migrations, seed data và observability.

Không kéo thêm dịch vụ chỉ vì “có thể dùng”. Đánh dấu dịch vụ bắt buộc, nên có và tùy chọn.

### 5. Đặc tả các luồng rủi ro cao

Viết sequence ngắn cho:

- Login/register/refresh/logout và lưu token. Không đưa secret vào frontend; ưu tiên httpOnly secure cookie hoặc mô hình token đã được quyết định.
- Checkout: validate item, tồn kho, promo, snapshot giá, transaction, idempotency key và payment.
- Reservation: search availability, hold, countdown, tạo reservation, thanh toán cọc, callback, confirm, cancel/refund.
- VNPay: ký HMAC-SHA512 ở server, verify checksum, allowlist return URL, đối chiếu amount/order, xử lý callback lặp và reconciliation.
- Admin cập nhật món, tồn kho, promotion, table, order và reservation.

Nêu race condition, retry, timeout, rollback và cách quan sát lỗi cho từng luồng. Không mô tả giữ bàn bằng cron nếu Redis TTL đã là nguồn hết hạn; nếu chọn cách khác phải giải thích rõ.

### 6. Lập kế hoạch chuyển từ mock sang API thật

Sắp xếp theo vertical slice, ưu tiên:

1. Backend bootstrap, health check, config, database và seed.
2. Auth và `/users/me/`, sau đó interceptor và auth store phía frontend.
3. Read-only catalog: categories, foods, combos, branches, promotions, posts, reviews.
4. Cart/checkout/order với server-side pricing, stock và order history.
5. Reservation availability, Redis hold và cancellation policy.
6. VNPay sandbox, callback và trạng thái thanh toán.
7. Admin operations, recommendation service và chat/realtime nếu cần.
8. Xóa mock hoặc giữ feature flag có thời hạn, rồi kiểm thử production config.

Mỗi milestone phải ghi dependency, file frontend cần đổi, migration/API cần tạo, test bắt buộc và điều kiện hoàn thành. Tuân theo convention của repo: nếu lớp `src/api` đã cô lập data access thì thay implementation ở đó trước, chỉ sửa page/store khi contract hoặc auth lifecycle thực sự yêu cầu.

### 7. Xác minh và chất lượng

Trước khi kết luận:

- Chạy lệnh sẵn có như `npm run build` và `npm run lint` nếu dependency/environment cho phép.
- Kiểm tra mọi endpoint trong inventory có implementation owner và test owner.
- Đối chiếu response với TypeScript type, kể cả nullable, date, currency và enum status.
- Kiểm tra phân quyền, rate limit, CORS/CSRF, secret management, validation, logging và PII.
- Đề xuất unit, integration, API contract, concurrency, payment callback và end-to-end tests.
- Nêu rõ test chưa chạy hoặc phần không thể xác minh.

## Format đầu ra

Trả lời bằng tiếng Việt, ngắn gọn nhưng đủ để triển khai, theo thứ tự:

1. **Kết luận hiện trạng**: frontend đã có gì, còn mock ở đâu, rủi ro lớn nhất.
2. **Giả định và câu hỏi cần chốt**: chỉ hỏi các quyết định ảnh hưởng kiến trúc; nếu có thể, đưa default recommendation.
3. **Inventory API**: bảng endpoint, auth, request/response, lỗi chính và source file.
4. **Domain/schema**: entity, quan hệ, index/constraint và state transitions.
5. **Kiến trúc đề xuất**: stack, module, infra, security và lý do.
6. **Luồng quan trọng**: checkout, reservation/hold và payment callback.
7. **Roadmap milestone**: dependency, frontend touch points, migration và acceptance criteria.
8. **Test/DoD**: các kiểm thử và tiêu chí go-live.
9. **Việc làm ngay**: tối đa 5 việc cụ thể cho bước tiếp theo.

Mọi kết luận quan trọng phải gắn với file hoặc symbol đã đọc. Không bịa endpoint, field hay quy tắc nghiệp vụ; nếu chưa có bằng chứng, ghi là giả định hoặc câu hỏi mở. Không tự động chỉnh code trong workflow lập phương án này.

## Tiêu chí hoàn thành

Skill chỉ hoàn tất khi:

- Tất cả nhóm API được phát hiện từ repo đã được đưa vào inventory hoặc ghi rõ lý do loại bỏ.
- Contract không để client làm nguồn sự thật cho tiền, quyền, trạng thái, stock hoặc payment.
- Reservation hold và payment callback có xử lý conflict, hết hạn, retry và idempotency.
- Có thứ tự triển khai thực tế, không chỉ là danh sách công nghệ.
- Có test strategy và các giới hạn chưa xác minh.
- Người đọc có thể biến phương án thành ticket/migration/API spec mà không phải đọc lại toàn bộ frontend.
