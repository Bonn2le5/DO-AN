# YÊU CẦU THIẾT KẾ 2 CHỨC NĂNG QUẢN LÝ BÀN VÀ ĐẶT BÀN

Hệ thống nhà hàng Mộc cần triển khai 2 chức năng độc lập về giao diện nhưng liên kết với nhau về dữ liệu và nghiệp vụ.

## 1. Sơ đồ bàn (Table Management)

**Mục đích:** Quản lý sơ đồ bàn và phục vụ khách đến trực tiếp nhà hàng (Walk-in), không có đặt bàn trước.

### Quy trình nghiệp vụ

1. Nhân viên truy cập trang Sơ đồ bàn.
2. Hệ thống hiển thị danh sách bàn theo từng khu vực và chi nhánh.
3. Nhân viên lựa chọn bàn đang trống.
4. Nhập số lượng khách và thông tin khách hàng (nếu có).
5. Xác nhận nhận khách và tạo phiên phục vụ (Dining Session).
6. Tạo hóa đơn (Order) gắn với bàn và phiên phục vụ.
7. Nhân viên lựa chọn món ăn, số lượng và ghi chú.
8. Gửi món đến bộ phận bếp.
9. Trong quá trình phục vụ, nhân viên có thể tiếp tục thêm món vào hóa đơn hiện tại.
10. Khi khách dùng bữa xong, nhân viên tiến hành thanh toán và kết thúc phiên phục vụ.

### Quy trình kết thúc phục vụ

Nhân viên mở hóa đơn → Kiểm tra các món đã gọi → Thanh toán → Xác nhận CHECK-OUT → Đóng phiên phục vụ → Bàn chuyển sang trạng thái Chờ dọn → Nhân viên xác nhận đã dọn bàn → Bàn chuyển về trạng thái Trống.

## 2. Quản lý đặt bàn (Reservation Management)

**Mục đích:** Quản lý khách đã đặt bàn trước thông qua website hoặc được nhân viên tạo đặt bàn hộ.

### Quy trình nghiệp vụ

**Giai đoạn 1: Khách Check-in**

1. Khách hàng đã có thông tin đặt bàn đến nhà hàng.
2. Khách hàng thực hiện Check-in thông qua website hoặc nhân viên hỗ trợ Check-in tại nhà hàng.
3. Hệ thống ghi nhận thời gian Check-in và cập nhật trạng thái đặt bàn thành Đã Check-in.
4. Sau khi khách Check-in, nhân viên tiếp nhận yêu cầu và tiến hành lựa chọn, sắp xếp bàn phù hợp cho khách.
5. Nhân viên chỉ được chọn các bàn phù hợp với số lượng khách và đang có thể phục vụ.
6. Nhân viên xác nhận bàn được phân công và liên kết bàn với thông tin đặt chỗ.

**Lưu ý:** Khách Check-in không đồng nghĩa với việc bàn đã được sử dụng ngay. Trạng thái sử dụng bàn chỉ được cập nhật khi nhân viên xác nhận xếp bàn và bắt đầu phiên phục vụ.

**Giai đoạn 2: Xếp bàn và tạo hóa đơn**

Sau khi nhân viên xác nhận xếp bàn, quy trình phục vụ phải hoạt động tương tự chức năng Sơ đồ bàn (Table Management):

1. Tạo phiên phục vụ (Dining Session) gắn với Reservation và bàn được phân công.
2. Tạo hóa đơn (Order) cho phiên phục vụ.
3. Nhân viên lựa chọn món ăn và thêm vào hóa đơn.
4. Gửi món đến bộ phận bếp.
5. Nhân viên có thể tiếp tục thêm món trong suốt quá trình khách sử dụng dịch vụ.
6. Theo dõi trạng thái món ăn và hóa đơn.

**Giai đoạn 3: Check-out và kết thúc phục vụ**

Nhân viên mở hóa đơn
↓
Kiểm tra các món đã gọi
↓
Thanh toán
↓
Xác nhận CHECK-OUT
↓
Đóng phiên phục vụ (Dining Session)
↓
Cập nhật trạng thái đặt bàn thành Đã hoàn tất
↓
Bàn chuyển sang trạng thái Chờ dọn
↓
Nhân viên dọn bàn và xác nhận
↓
Bàn chuyển về trạng thái Trống

## 3. Nguyên tắc thiết kế và xử lý nghiệp vụ

- Hai chức năng Table Management và Reservation Management phải sử dụng chung hệ thống bàn, Order, Dining Session và Payment.
- Không xây dựng hai quy trình tạo hóa đơn riêng biệt.
- Khách Walk-in tạo Dining Session trực tiếp từ sơ đồ bàn, không cần Reservation.
- Khách đặt bàn phải Check-in trước, sau đó nhân viên mới thực hiện xếp bàn và bắt đầu phiên phục vụ.
- Reservation không tự động tạo hóa đơn ngay khi khách đặt bàn hoặc Check-in.
- Chỉ tạo Order khi khách đã được nhân viên xác nhận xếp bàn và bắt đầu phục vụ.
- Mỗi bàn không được có nhiều Dining Session đang hoạt động đồng thời.
- Khi thanh toán hoàn tất và Check-out, bàn chuyển sang Chờ dọn, không chuyển thẳng về Trống.
- Chỉ khi nhân viên xác nhận dọn bàn xong thì bàn mới trở về trạng thái Trống.
- Toàn bộ dữ liệu phải được giới hạn theo chi nhánh: Admin tổng được quản lý tất cả chi nhánh, Quản lý chi nhánh và nhân viên chỉ thao tác trong phạm vi được phân quyền.

## 4. Yêu cầu giao diện

Thiết kế hai trang riêng biệt:

1. **Table Management:** Giao diện sơ đồ bàn trực quan, hiển thị trạng thái bàn theo màu sắc, khu vực, sức chứa và thông tin phiên phục vụ. Cho phép chọn bàn, tạo hóa đơn và quản lý món ăn ngay tại bàn.
2. **Reservation Management:** Giao diện danh sách đặt bàn, lịch đặt bàn, thông tin khách hàng, trạng thái Check-in và chức năng xếp bàn cho khách. Khi đã xếp bàn, cho phép truy cập trực tiếp phiên phục vụ và hóa đơn tương ứng.

Giao diện cần hiện đại, dễ thao tác

## 5. Phân chia giao diện Admin và nhân viên

Chức năng Admin tổng Quản lý chi nhánh Nhân viên
Xem sơ đồ bàn Tất cả Chi nhánh mình Chi nhánh mình
Tạo hóa đơn Có Có Có
Chuyển bàn Có Có Theo quyền
Check-in Có Có Có
Check-out Có Có Có
Quản lý đặt bàn Tất cả Chi nhánh mình Theo quyền
Cấu hình bàn Tất cả Chi nhánh mình Không
