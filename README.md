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

### 4. Ghi log chấm công (Timesheet)
- Ghi nhận dữ liệu nhận diện khuôn mặt vào file log
- Đẩy dữ liệu chấm công lên hệ thống QCD

---

## ⚙️ Cấu hình giao diện (UI Options)

Truy cập: **Cài đặt → Thiết bị & Dịch vụ → Javis Hanet → Cấu hình (Configure)**

| Tùy chọn | Kiểu | Mặc định | Mô tả |
|---|---|---|---|
| **Selected Places** | Multi-select | — | Chọn các địa điểm cần giám sát |
| **HRM Sync Enabled** | Toggle | `Tắt` | Bật/tắt đồng bộ tự động từ HRM |
| **HRM Sync Log Enabled** | Toggle | `Tắt` | Bật/tắt ghi log debug cho luồng sync |
| **HRM Sync Interval** | Number | `30` (giây) | Chu kỳ polling dữ liệu (tối thiểu 5s) |

---

## 🔧 Danh sách Service

Tất cả service có thể gọi từ **Công cụ nhà phát triển → Dịch vụ** hoặc từ **Automation**.

### `javis_hanet.write_person`
Ghi dữ liệu nhận diện vào file log chấm công.

| Tham số | Bắt buộc | Mô tả |
|---|---|---|
| `payload` | ✅ | Chuỗi JSON chứa thông tin nhận diện |

---

### `javis_hanet.push_to_qcd`
Đẩy dữ liệu log chấm công lên hệ thống QCD.

| Tham số | Bắt buộc | Mô tả |
|---|---|---|
| `secret_key` | ✅ | Khóa xác thực QCD |
| `date` | ❌ | Ngày cụ thể (YYYY-MM-DD), mặc định hôm nay |

---

### `javis_hanet.update_period`
Cập nhật thời gian mở cửa cho 1 nhân sự.

| Tham số | Bắt buộc | Mô tả |
|---|---|---|
| `person_id` | ✅ | Mã nhân sự Hanet |
| `start_time` | ❌ | Ngày bắt đầu |
| `end_time` | ❌ | Ngày kết thúc |

---

### `javis_hanet.check_faceid_group_sensor`
Kiểm tra và cập nhật lại sensor nhóm FaceID. Không có tham số.

---

### `javis_hanet.sync_periods`
Đồng bộ thời gian mở cửa từ server. Không có tham số.

---

### `javis_hanet.set_hrm_sync_interval`
Thay đổi chu kỳ đồng bộ HRM (có hiệu lực ngay lập tức).

| Tham số | Bắt buộc | Mô tả |
|---|---|---|
| `interval` | ✅ | Số giây giữa mỗi lần polling (tối thiểu 5) |

---

### `javis_hanet.set_hrm_sync_enabled`
Bật hoặc tắt tính năng đồng bộ tự động từ HRM.

| Tham số | Bắt buộc | Mô tả |
|---|---|---|
| `enabled` | ✅ | `true` để bật, `false` để tắt |

---

### `javis_hanet.set_hrm_sync_log_enabled`
Bật hoặc tắt việc ghi log debug cho luồng sync HRM.

| Tham số | Bắt buộc | Mô tả |
|---|---|---|
| `enabled` | ✅ | `true` để hiện log, `false` để chạy im lặng |

---

## 📁 Cấu trúc file

```
main_code/2024/
├── __init__.py       # Logic chính: setup entry, đăng ký service, background sync
├── config_flow.py    # Luồng cấu hình giao diện (OAuth + Options Flow)
├── const.py          # Hằng số: domain, URL API, service names
├── hrm_api.py        # Client gọi API HRM (token, queue, ACK)
├── utils.py          # Hàm tiện ích: đọc/ghi JSON, YAML, URL helper
├── services.yaml     # Đặc tả service cho giao diện HA
├── encode.py         # Biên dịch .py → .pyc khi release
├── manifest.json     # Metadata component
└── strings.json      # Chuỗi hiển thị giao diện

tests/
├── conftest.py          # Ánh xạ main_code/2024 → custom_components.javis_hanet
├── run_all.py           # Chạy toàn bộ test suite 1 lệnh
├── test_proof.py        # Smoke test: đường dẫn, DOMAIN, hàm core
├── test_utils.py        # YAML I/O, URL helper, version check
├── test_architecture.py # File lock, regex YAML, merge data, expiration
├── test_sync_logic.py   # Extract place_id, queue items, partial update
├── test_hrm_api.py      # HRMClient: token, queue fetch, ACK
└── test_integrity.py    # Toàn vẹn cấu hình (services ↔ const, manifest)
```

---

## 🧪 Chạy test

### Yêu cầu môi trường

```bash
# Tạo môi trường Conda riêng (chỉ cần làm 1 lần)
conda create -y -n javis_ha_test python=3.12
conda activate javis_ha_test
pip install pytest pytest-homeassistant-custom-component pytest-asyncio
```

### Chạy test

```bash
# Kích hoạt môi trường
conda activate javis_ha_test

# Chạy toàn bộ (khuyên dùng)
python tests/run_all.py

# Chạy từng file riêng lẻ
python tests/test_proof.py
python tests/test_hrm_api.py
```

### Cơ chế hoạt động

Tất cả file test đều import trực tiếp từ `main_code/2024/` thông qua `conftest.py`.
File `conftest.py` đăng ký một custom importer vào `sys.meta_path`, ánh xạ namespace
`custom_components.javis_hanet` → thư mục `main_code/2024/`. Nhờ đó, mọi thay đổi
trong code gốc sẽ được test phát hiện ngay lập tức.

> **Lưu ý:** Trên Windows, `pytest` bị crash do xung đột giữa `pytest-socket` (chặn socket)
> và `ProactorEventLoop` (cần socket nội bộ). Vì vậy test được chạy trực tiếp bằng `python`
> thay vì `pytest`. Trên Linux/WSL, có thể dùng `pytest tests/ -v` bình thường.

---

## 🔐 Lưu ý bảo mật

- File `api_doc.txt` chứa thông tin API nhạy cảm đã được **untrack khỏi Git**
- Các thông tin xác thực HRM (`CLIENT_ID`, `CLIENT_SECRET`) lưu trong `const.py`
- File `person_javis_v2.json` chứa dữ liệu nhân sự đã được thêm vào `.gitignore`
