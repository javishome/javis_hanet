# Javis Hanet Component

## Chức năng chính
### Ngày 09/09/2026 (Version v20260909)
- Bản build Universal duy nhất tương thích mọi phiên bản Home Assistant Core (2024.x, 2025.x, 2026.x+).
- Tự động mã hóa bảo vệ mã nguồn qua Universal Dynamic Encrypted Loader (nạp động trên RAM).
- Khởi tạo bất đồng bộ `async_setup` tuân thủ chuẩn Event Loop Thread-Safety của HA.
- Tích hợp ma trận kiểm thử 2 tầng tự động trên 5 mốc HA Core khi chạy `auto_encode.py`.
- Chuẩn hóa cấu trúc: mã nguồn gốc tại `main_code/`, bản build xuất thẳng vào `build/`.
- Chuẩn hóa Release Tag dạng `vYYYYMMDD` đồng bộ liên thông HACS và Server Version Policy.

### Ngày 22/08/2026 (Version v20260822)
- Xử lý đọc/ghi file bất đồng bộ (Async) tránh đơ Home Assistant.
- Tự động biên dịch file `.pyc` bảo mật khi commit.
- Tối ưu pipeline CI/CD build siêu tốc (~5 giây).
- Bổ sung bộ test và linter kiểm tra toàn bộ 8 services.

### Ngày 05/05/2026
- Sửa lỗi sinh OAuth callback URL trên Home Assistant 2025 bằng cách lấy định danh HC từ interface thiết bị (`eth0`, fallback `end0`) thay vì `uuid.getnode()`.
- Cải thiện tương thích Home Assistant 2025 cho config/options flow, gồm `OptionsFlow`, reauth, xử lý lỗi OAuth và cleanup config flow.

### Ngày 20/4/2026
- Tích hợp Hanet Camera qua OAuth 2.0 và kết nối AI Box qua IP/Port/Key.
- Tự động đồng bộ danh sách nhân sự, camera, vị trí vào file `person_javis_v2.json`.
- Đồng bộ tự động từ hàng đợi HRM (`/hc/auto-open-queue`) và phản hồi ACK.
- Hỗ trợ đầy đủ 8 services: ghi nhận diện chấm công, đẩy QCD, cập nhật period, đồng bộ HRM.
- Tự động dọn dẹp các period hết hạn hàng ngày vào 00:05.
