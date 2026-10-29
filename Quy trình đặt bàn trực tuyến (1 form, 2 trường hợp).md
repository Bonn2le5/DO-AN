# Quy trình đặt bàn trực tuyến (1 form, 2 trường hợp)

Tài liệu tổng hợp quy trình đặt bàn sau khi gộp hai hình thức "Chỉ đặt bàn" và "Đặt bàn + Gọi món trước" thành một form duy nhất. Các con số như mức cọc 30% và thời hạn hoàn cọc 4 giờ là dữ liệu mẫu trong mockup, cần nhà hàng xác nhận trước khi áp dụng thật.

## 1. Mục tiêu và nguyên tắc

Quy trình cũ yêu cầu khách chọn hình thức ngay từ đầu, gồm 5 bước: Hình thức, Chọn bàn, Chọn món, Xác nhận, Đặt cọc. Quy trình mới bỏ bước chọn hình thức và rút còn 3 bước.

Nguyên tắc chính:

- Chỉ có một form. Khách không phải chọn "mình thuộc trường hợp nào".
- Hệ thống tự phân biệt trường hợp dựa vào giỏ món: giỏ trống là chỉ đặt bàn, giỏ có món là đặt bàn kèm gọi món trước.
- Chỉ khi có món thì mới tính tiền và yêu cầu đặt cọc.
- Cả hai trường hợp đều kết thúc bằng việc chờ nhà hàng gọi điện xác nhận.
- Dữ liệu khách đã nhập không bị mất khi bấm Quay lại.

## 2. Tổng quan luồng

| Bước | Tên      | Nội dung                                                  | Bắt buộc |
| ---- | -------- | --------------------------------------------------------- | -------- |
| 1    | Đặt chỗ  | Chi nhánh, ngày, giờ, số người, chọn bàn nếu có           | Có       |
| 2    | Gọi món  | Chọn món ăn dùng trước                                    | Không    |
| 3    | Xác nhận | Thông tin liên hệ, tóm tắt đơn, thanh toán cọc nếu có món | Có       |

So với quy trình cũ:

| Cũ           | Mới                                     |
| ------------ | --------------------------------------- |
| 1. Hình thức | Bỏ hẳn                                  |
| 2. Chọn bàn  | Gộp vào bước 1 Đặt chỗ                  |
| 3. Chọn món  | Thành bước 2 Gọi món, không bắt buộc    |
| 4. Xác nhận  | Thành bước 3 Xác nhận                   |
| 5. Đặt cọc   | Gộp vào bước 3, chỉ hiện khi giỏ có món |

## 3. Chi tiết từng bước

### Bước 1: Đặt chỗ

- Khách chọn chi nhánh, ngày, giờ, số người và bàn (nếu hệ thống cho chọn bàn).
- Nút chính: **Tiếp tục**.
- Nếu khách chọn khung giờ cao điểm hoặc dịp lễ, bước 2 sẽ hiện dòng gợi ý gọi món trước.

### Bước 2: Gọi món trước (không bắt buộc)

**Nội dung màn hình**

- Tiêu đề: "Gọi món trước?". Mô tả ngắn giải thích món được chuẩn bị sẵn và khách có thể bỏ qua để gọi món khi đến.
- Dòng gợi ý nhỏ cho giờ cao điểm, thay cho nhãn "Khuyên dùng" ở thiết kế cũ.
- Thanh lọc theo nhóm món: Tất cả, Khai vị, Món chính, Tráng miệng.
- Mỗi món hiển thị ảnh, tên, giá và nút **Thêm món** (kích thước nhỏ). Không hiển thị mô tả nguyên liệu.
- Khi đã thêm món, nút Thêm món chuyển thành bộ tăng giảm số lượng.

**Khung "Món đã chọn"**

- Chỉ hiện khi giỏ có món, nằm phía trên thanh lọc nhóm.
- Mỗi dòng gồm ảnh nhỏ, tên món, giá và bộ tăng giảm số lượng.
- Giảm số lượng về 0 thì món biến mất khỏi khung. Giỏ trống thì khung tự ẩn.

**Thanh dưới cùng**

| Trạng thái giỏ | Hiển thị                       | Nút          |
| -------------- | ------------------------------ | ------------ |
| Trống          | "Chưa chọn món nào"            | **Bỏ qua**   |
| Có món         | Số món, tổng tiền, cọc dự kiến | **Tiếp tục** |

Cả hai nút đều dẫn sang bước 3.

**Nút Quay lại**

- Nằm ở góc trên bên trái, có ở bước 2 và bước 3. Bước 1 không có.
- Quay về bước 1 không làm mất lựa chọn đã nhập.

### Bước 3: Xác nhận

**Phần chung cho cả hai trường hợp**

- Họ và tên (bắt buộc).
- Số điện thoại (chữ mờ " chọn số có Zalo).
- Ghi chú (không bắt buộc), ví dụ có trẻ em, cần ghế em bé.
- Dòng thông báo: nhà hàng sẽ gọi điện xác nhận với khách.

**Phần thay đổi theo giỏ món**

|                | Trường hợp 1: giỏ trống  | Trường hợp 2: giỏ có món                                     |
| -------------- | ------------------------ | ------------------------------------------------------------ |
| Danh sách món  | Không hiện               | Hiện từng món, số lượng, thành tiền                          |
| Tổng tiền món  | Không hiện               | Hiện                                                         |
| Thanh toán cọc | **Ẩn hoàn toàn**         | Hiện số tiền cọc, phương thức thanh toán, điều kiện hoàn cọc |
| Nút chính      | **Xác nhận đặt chỗ**     | **Thanh toán cọc & đặt chỗ**                                 |
| Sau khi gửi    | "Đã gửi yêu cầu đặt chỗ" | "Đã nhận cọc và đặt chỗ"                                     |

**Kiểm tra dữ liệu trước khi gửi**

- Thiếu họ tên: báo "Nhập họ và tên để nhà hàng liên hệ."
- Số điện thoại sai định dạng: báo "Nhập số điện thoại gồm 10 số, bắt đầu bằng 0."
- Báo lỗi ngay dưới ô nhập, không xoá dữ liệu khách đã điền.

## 4. Hai trường hợp sử dụng

### Trường hợp 1: Chỉ đặt bàn

1. Khách chọn chi nhánh, ngày, giờ, số người ở bước 1.
2. Ở bước 2, khách bấm **Bỏ qua** vì không chọn món.
3. Ở bước 3, khách nhập họ tên, số điện thoại, ghi chú.
4. Khách bấm **Xác nhận đặt chỗ**. Không có thanh toán.
5. Đơn chuyển sang trạng thái **Chờ xác nhận (chưa cọc)**.
6. Nhà hàng gọi điện xác nhận.

### Trường hợp 2: Đặt bàn kèm gọi món trước

1. Khách chọn chi nhánh, ngày, giờ, số người ở bước 1.
2. Ở bước 2, khách thêm món và chỉnh số lượng. Hệ thống cập nhật tổng tiền và cọc dự kiến theo thời gian thực.
3. Khách bấm **Tiếp tục** sang bước 3.
4. Khách nhập họ tên, số điện thoại, ghi chú, xem tóm tắt món và số tiền cọc, chọn phương thức thanh toán.
5. Khách bấm **Thanh toán cọc & đặt chỗ**.
6. Thanh toán thành công, đơn chuyển sang trạng thái **Chờ xác nhận (đã cọc)**.
7. Nhà hàng gọi điện xác nhận.

## 5. Quy tắc xử lý dữ liệu

- Toàn bộ dữ liệu (giỏ món, nhóm món đang lọc, họ tên, số điện thoại, ghi chú, phương thức thanh toán) được giữ trong suốt phiên đặt chỗ, kể cả khi khách bấm Quay lại.
- Khách quay lại bước 2 và xoá hết món thì khi sang bước 3, phần thanh toán tự ẩn và nút chính đổi về "Xác nhận đặt chỗ".
- Khách thêm món sau khi đã từng bỏ qua thì bước 3 tự hiện phần cọc.
- Tổng tiền và tiền cọc luôn được tính lại từ giỏ món hiện tại, không lưu số cũ.

## 6 Kết luận

1. Xác định nhu cầu: gộp hai hình thức thành một form, không bắt khách chọn.
2. Rút luồng từ 5 bước còn 3 bước và mô tả logic ẩn hiện phần cọc.
   3 gọi món trước, có thanh bỏ qua và cọc 25% .
3. món có ảnh và giá, bỏ mô tả nguyên liệu, thu nhỏ nút Thêm món, thêm khung Món đã chọn, thêm nút Quay lại và bước 3 Xác nhận, giữ dữ liệu khi quay lại.
