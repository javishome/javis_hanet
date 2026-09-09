# Javis Hanet Component

## Chức năng chính
### Ngày 09/09/2026 (Version v20260909)
- **1 bản cài đặt duy nhất**: Tương thích mượt mà với mọi phiên bản Home Assistant (từ HA 2024 đến HA 2025+).
- **Bảo vệ mã nguồn an toàn**: Tự động mã hóa code bảo mật mà không làm ảnh hưởng đến tốc độ chạy.
- **Khởi chạy mượt mà**: Sửa lỗi luồng, đảm bảo không bị treo khi Home Assistant khởi động và gọi các dịch vụ đồng bộ.
- **Kiểm thử toàn diện**: Đạt 100% trên các bài test tự động và thiết bị Home Assistant thực tế.
- **Tối ưu cập nhật**: Chuẩn hóa đóng gói để cài đặt và nâng cấp dễ dàng, ổn định qua HACS.

### Ngày 22/08/2026 (Version v20260822)
- Xử lý đọc/ghi file bất đồng bộ (Async) tránh đơ Home Assistant.
- Tự động biên dịch bảo mật khi commit.
- Tối ưu pipeline build nhanh và ổn định.
- Bổ sung bộ test kiểm tra toàn bộ 8 services.

### Ngày 05/05/2026
- Sửa lỗi tạo đường dẫn OAuth callback trên Home Assistant 2025.
- Cải thiện luồng cấu hình, đăng nhập lại (reauth) và xử lý lỗi kết nối.

### Ngày 20/4/2026
- Tích hợp camera Hanet qua tài khoản OAuth 2.0 và kết nối AI Box qua IP/Port/Key.
- Tự động đồng bộ danh sách nhân sự, camera, vị trí vào file `person_javis_v2.json`.
- Tự động đồng bộ lịch mở cửa từ hàng đợi HRM và phản hồi xác nhận (ACK).
- Hỗ trợ đầy đủ 8 dịch vụ: ghi log chấm công, đẩy dữ liệu lên QCD, cập nhật thời gian mở cửa, đồng bộ HRM.
- Tự động dọn dẹp các quyền mở cửa hết hạn vào 00:05 hàng ngày.
