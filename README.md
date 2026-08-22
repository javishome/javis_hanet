# Javis Hanet - Custom Component cho Home Assistant

> Tích hợp hệ thống nhận diện khuôn mặt Hanet / AI Box vào Home Assistant, kèm tính năng đồng bộ tự động dữ liệu thời gian mở cửa (period) từ hệ thống HRM.

---

## Cập nhật ngày 22/08/2026 (Version v20260822)

- **Chuyển đổi Async File I/O**: Chuyển các thao tác đọc/ghi file đồng bộ (xoay vòng log QCD, `handle_write_person`, `yaml2dict`) sang `asyncio.to_thread` và `async_add_executor_job` để không block event loop của Home Assistant.
- **Tương thích HA 2025/2026**: Bổ sung fallback import `ConfigFlowResult` cho config flow.
- **Tự động Compile Bytecode (.pyc)**: Tích hợp `auto_encode.py` tự động nhận diện Python 3.12/3.13 và compile vào Pre-commit Hook.
- **Tối ưu CI/CD Pipeline**: Chuyển sang Docker `alpine:latest` giúp sync release lên GitHub trong ~5 giây.
- **Kiểm thử & Linter**: Bổ sung test tự động toàn diện cho 100% 8 Service (`sync_periods`, `update_period`, `push_to_qcd`, `check_faceid_group_sensor`, `set_hrm_sync_*`).

---

## Cập nhật ngày 05/05/2026

- Sửa lỗi sinh OAuth callback URL trên Home Assistant 2025 bằng cách lấy định danh HC từ interface thiết bị (`eth0`, fallback `end0`) thay vì `uuid.getnode()`.
- Cải thiện tương thích Home Assistant 2025 cho config/options flow, gồm `OptionsFlow`, reauth, xử lý lỗi OAuth và cleanup config flow.

---

## 📋 Tính năng chính
### Ngày 20/4/2026
#### 1. Kết nối Hanet Camera
- Đăng nhập qua **OAuth 2.0** với tài khoản Hanet
- Chọn địa điểm (Place) cần giám sát
- Tự động đồng bộ danh sách nhân sự, camera, vị trí vào file `person_javis_v2.json`

#### 2. Kết nối AI Box
- Kết nối trực tiếp qua **IP + Port + Key**
- Lấy danh sách profile từ thiết bị AI Box local

#### 3. Đồng bộ tự động từ HRM (Auto Queue Sync)
- Polling dữ liệu hàng đợi từ API HRM (`/hc/auto-open-queue`) theo chu kỳ cấu hình
- Tự động cập nhật `start_time` / `end_time` cho nhân sự trong file JSON
- Gửi phản hồi ACK về HRM sau khi xử lý xong
- Token OAuth 2.0 được cache và tự động refresh khi sắp hết hạn

#### 4. Hỗ trợ service cài đặt mở cửa, đồng bộ lên HRM
- khi nhận được yêu cầu cài đặt mở cửa, tự động cập nhập file `person_javis_v2.json`

#### 5. Ghi log chấm công (Timesheet)
- Ghi nhận dữ liệu nhận diện khuôn mặt vào file log
- Đẩy dữ liệu chấm công lên hệ thống QCD

---
