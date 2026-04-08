# Javis Hanet - Custom Component cho Home Assistant

> Tích hợp hệ thống nhận diện khuôn mặt Hanet / AI Box vào Home Assistant, kèm tính năng đồng bộ tự động dữ liệu thời gian mở cửa (period) từ hệ thống HRM.

---

## 📋 Tính năng chính

### 1. Kết nối Hanet Camera
- Đăng nhập qua **OAuth 2.0** với tài khoản Hanet
- Chọn địa điểm (Place) cần giám sát
- Tự động đồng bộ danh sách nhân sự, camera, vị trí vào file `person_javis_v2.json`

### 2. Kết nối AI Box
- Kết nối trực tiếp qua **IP + Port + Key**
- Lấy danh sách profile từ thiết bị AI Box local

### 3. Đồng bộ tự động từ HRM (Auto Queue Sync)
- Polling dữ liệu hàng đợi từ API HRM (`/hc/auto-open-queue`) theo chu kỳ cấu hình
- Tự động cập nhật `start_time` / `end_time` cho nhân sự trong file JSON
- Gửi phản hồi ACK về HRM sau khi xử lý xong
- Token OAuth 2.0 được cache và tự động refresh khi sắp hết hạn

### 4. Hỗ trợ service cài đặt mở cửa, đồng bộ lên HRM
- khi nhận được yêu cầu cài đặt mở cửa, tự động cập nhập file `person_javis_v2.json`

### 4. Ghi log chấm công (Timesheet)
- Ghi nhận dữ liệu nhận diện khuôn mặt vào file log
- Đẩy dữ liệu chấm công lên hệ thống QCD

---