# Hướng dẫn kiểm thử (code + thực tế)

Tài liệu này hướng dẫn 2 loại kiểm thử:
- **Kiểm thử code**: chạy bằng script Python trong thư mục `tests/`
- **Kiểm thử thực tế (manual)**: dành cho các luồng cần môi trường Home Assistant thật, thiết bị thật hoặc API thật

Repository này giữ chuẩn hiện tại: mỗi test chạy bằng lệnh `python tests/test_xxx.py`.

## 1) Điều kiện chuẩn bị

### 1.1 Cho kiểm thử code
- Python 3.12+
- Cài các thư viện cần thiết:
  - `pytest`
  - `pytest-homeassistant-custom-component`
  - `pytest-asyncio`
  - `voluptuous`

Ví dụ cài đặt:

```bash
pip install pytest pytest-homeassistant-custom-component pytest-asyncio voluptuous
```

### 1.2 Cho kiểm thử thực tế
- Có môi trường Home Assistant đã cài integration này
- Có tài khoản Hanet hợp lệ (OAuth) và/hoặc thiết bị AI Box (`ip`, `port`, `key`)
- Host HA truy cập được API HRM
- Có quyền xem log HA và đọc file `/config/person_javis_v2.json`

## 2) Cách chạy test code

### 2.1 Chạy toàn bộ

```bash
python tests/run_all.py
```

### 2.2 Chạy từng test lẻ

```bash
python tests/test_versioning.py
python tests/test_services_registration.py
python tests/test_service_update_period.py
python tests/test_sync_periods_api.py
```

## 3) Bản đồ coverage hiện tại

### 3.1 Các test có sẵn trước đó
- `tests/test_run.py`
  - Đầu vào: import module/class chính
  - Đầu ra mong đợi: import thành công
  - Lưu ý: chỉ là smoke test

- `tests/test_proof.py`
  - Đầu vào: import alias + kiểm tra symbol quan trọng
  - Đầu ra mong đợi: test trỏ đúng vào `main_code/2024`
  - Lưu ý: dùng để chứng minh đường dẫn import

- `tests/test_utils.py`
  - Đầu vào: dữ liệu YAML/utility helper
  - Đầu ra mong đợi: kết quả parse/convert đúng
  - Lưu ý: coverage ở mức utility

- `tests/test_sync_logic.py`
  - Đầu vào: dữ liệu queue/person mẫu
  - Đầu ra mong đợi: cập nhật dữ liệu + ACK logic đúng
  - Lưu ý: mô phỏng logic, chưa phải runtime đầy đủ của HA

- `tests/test_hrm_api.py`
  - Đầu vào: response HTTP được mock
  - Đầu ra mong đợi: token/queue/ack trả đúng theo từng nhánh
  - Lưu ý: không gọi mạng thật

### 3.2 Các test mới đã bổ sung

- `tests/test_versioning.py`
  - **V-001**
    - Đầu vào: `v1`
    - Đầu ra mong đợi: `v2`
    - Lưu ý: luồng chuẩn cho format mới
  - **V-002**
    - Đầu vào: `1`
    - Đầu ra mong đợi: `v2`
    - Lưu ý: tương thích ngược với format cũ
  - **V-003**
    - Đầu vào: `V9`
    - Đầu ra mong đợi: `v10`
    - Lưu ý: không phân biệt hoa/thường ở tiền tố `v`
  - **V-004**
    - Đầu vào: `vx`, `1.2`, rỗng, `v`
    - Đầu ra mong đợi: raise `ValueError`
    - Lưu ý: chỉ chấp nhận `v<digits>` hoặc `<digits>`
  - **V-005 / V-006 / V-007**
    - Đầu vào: file manifest tạm (`v1`, `1`, hoặc sai format)
    - Đầu ra mong đợi: cặp `(old, new)` đúng + hành vi ghi file đúng
    - Lưu ý: xác nhận đường đi an toàn khi dữ liệu lỗi

- `tests/test_services_registration.py`
  - **SR-001**
    - Đầu vào: gọi `Services.register_new()`
    - Đầu ra mong đợi: đăng ký đủ 8 service
    - Lưu ý: gồm cả toggle HRM enable/log
  - **SR-002**
    - Đầu vào: gọi `Services.register_old()`
    - Đầu ra mong đợi: đăng ký 6 service legacy
    - Lưu ý: không có `set_hrm_sync_enabled/log_enabled` ở luồng cũ
  - **SR-003**
    - Đầu vào: validate schema cho service write/interval/enabled
    - Đầu ra mong đợi: field bắt buộc và coercion đúng
    - Lưu ý: kiểm tra contract đầu vào của service

- `tests/test_service_update_period.py`
  - **UP-001**
    - Đầu vào: `person_id` tồn tại, `end_time` tương lai
    - Đầu ra mong đợi: `status=ok`, lưu dữ liệu, gọi API cập nhật
    - Lưu ý: không đi vào nhánh cleanup expired
  - **UP-002**
    - Đầu vào: `person_id` không tồn tại
    - Đầu ra mong đợi: `status=error`, không lưu file, không gọi API
    - Lưu ý: kiểm tra early-return guard
  - **UP-003**
    - Đầu vào: `person_id` tồn tại, `end_time` quá hạn
    - Đầu ra mong đợi: `status=ok`, gọi remove PID + reload MQTT
    - Lưu ý: xác nhận nhánh hết hạn

- `tests/test_sync_periods_api.py`
  - **SP-001**
    - Đầu vào: danh sách person trộn (có/không có `person_id`), HTTP 200
    - Đầu ra mong đợi: trả `True`, payload chỉ giữ record hợp lệ
    - Lưu ý: kiểm tra lọc payload trước khi gửi
  - **SP-002**
    - Đầu vào: HTTP 500
    - Đầu ra mong đợi: trả `False`
    - Lưu ý: đảm bảo caller xử lý nhánh lỗi

- `tests/test_hrm_auto_cleanup.py`
  - **HC-001**
    - Đầu vào: HRM sync bật, dữ liệu person không có `place_id`
    - Đầu ra mong đợi: vẫn gọi luồng cleanup hết hạn
    - Lưu ý: xác nhận cleanup chạy mỗi vòng sync, không phụ thuộc queue
  - **HC-002**
    - Đầu vào: HRM queue rỗng
    - Đầu ra mong đợi: vẫn gọi cleanup, không gọi ACK queue
    - Lưu ý: queue rỗng vẫn phải dọn person hết hạn
  - **HC-003**
    - Đầu vào: cleanup trả `True` hoặc `False`
    - Đầu ra mong đợi: chỉ reload MQTT khi cleanup có thay đổi thật
    - Lưu ý: tránh reload MQTT không cần thiết

## 4) Những phần chưa coverage đầy đủ bằng code

Các phần sau cần test thật trên HA:
- OAuth flow đầy đủ trong UI (`config_flow.py`)
- Kết nối Hanet cloud thật + chọn place thật
- Kết nối AI Box thật (`ip/port/key`)
- End-to-end HRM polling + ACK trên API thật
- Side-effect thật trên file/sensor/MQTT (`/config/packages/face_sensor.yaml`, MQTT reload)

## 5) Kịch bản test thực tế bắt buộc

Mỗi kịch bản cần ghi:
- Đầu vào / điều kiện trước test
- Kết quả thực tế
- Bằng chứng (log/screenshot/trích file trước-sau)
- Lưu ý

### M-001 Cấu hình Hanet OAuth
- Đầu vào/Điều kiện:
  - Tài khoản Hanet hợp lệ
  - URL HA hoạt động bình thường
- Bước thực hiện:
  1. Add integration `Javis Hanet`
  2. Chọn `hanet`
  3. Hoàn tất OAuth và chọn place
- Đầu ra mong đợi:
  - Tạo config entry thành công
  - `person_javis_v2.json` có dữ liệu place/person tương ứng
- Lưu ý:
  - Không xuất hiện abort reason trên UI

### M-002 Cấu hình AI Box
- Đầu vào/Điều kiện:
  - AI Box online với thông số đúng (`ip`, `port`, `key`)
- Bước thực hiện:
  1. Add integration
  2. Chọn `ai_box`
  3. Nhập thông số kết nối
- Đầu ra mong đợi:
  - Entry tạo thành công (title dạng `AI Box (<ip>)`)
  - Lấy được danh sách profile từ `/api/Profile`
- Lưu ý:
  - Test thêm 1 case key sai, mong đợi `cannot_connect`

### M-003 HRM auto sync background
- Đầu vào/Điều kiện:
  - `hrm_sync_enabled=true`
  - Có `place_id` trong file local
  - HRM queue có ít nhất 1 item `upsert`
- Bước thực hiện:
  1. Bật HRM sync ở options
  2. Đặt interval (ví dụ 30s)
  3. Chờ qua ít nhất 1 chu kỳ polling
- Đầu ra mong đợi:
  - `start_time/end_time` local được cập nhật
  - Có request ACK gửi lên HRM
- Lưu ý:
  - Chụp log đoạn fetch queue + ACK

### M-004 Service `update_period`
- Đầu vào/Điều kiện:
  - `person_id` tồn tại trong file local
- Bước thực hiện:
  1. Gọi service `javis_hanet.update_period`
  2. Payload mẫu:

```yaml
person_id: "p001"
start_time: "2026-01-01"
end_time: "2026-12-31"
```

- Đầu ra mong đợi:
  - Response service có `status: ok`
  - File person local được cập nhật đúng
  - API cập nhật period được gọi
- Lưu ý:
  - Test thêm case `person_id` không tồn tại -> mong đợi `status: error`

### M-005 Dọn người hết hạn + reload MQTT
- Đầu vào/Điều kiện:
  - Có person đã hết hạn (`end_time` <= ngày hiện tại)
  - `face_sensor.yaml` có chứa `person_id` trong `value_template`
- Bước thực hiện:
  1. Gọi `javis_hanet.check_faceid_group_sensor`
  2. Kiểm tra file `face_sensor.yaml` + log HA
- Đầu ra mong đợi:
  - `person_id` hết hạn bị loại khỏi template
  - MQTT được reload thành công
- Lưu ý:
  - Đảm bảo regex không làm hỏng ID khác (ví dụ xóa `1` không làm ảnh hưởng `12`)

### M-006 Service `sync_periods`
- Đầu vào/Điều kiện:
  - File local có person với `person_id`
- Bước thực hiện:
  1. Gọi `javis_hanet.sync_periods`
  2. Kiểm tra payload gửi đi + response
- Đầu ra mong đợi:
  - HTTP 200 -> `status: ok`
  - HTTP != 200 -> `status: error`
- Lưu ý:
  - Record không có `person_id` phải bị bỏ qua

### M-007 Runtime toggle services
- Đầu vào/Điều kiện:
  - Integration đang hoạt động
- Bước thực hiện:
  1. Gọi `javis_hanet.set_hrm_sync_enabled`
  2. Gọi `javis_hanet.set_hrm_sync_log_enabled`
  3. Gọi `javis_hanet.set_hrm_sync_interval`
- Đầu ra mong đợi:
  - Option mới có hiệu lực ngay
  - Lịch polling cập nhật theo interval mới
- Lưu ý:
  - Interval tối thiểu phải >= 5

## 6) Mẫu biên bản test

Dùng mẫu sau cho mỗi kịch bản manual:

```text
Mã test:
Thời gian:
Người test:
Môi trường (HA version, account type, endpoint):

Đầu vào/Điều kiện:
Các bước thực hiện:
Đầu ra mong đợi:
Đầu ra thực tế:
Bằng chứng (log/screenshot/trích file):
Lưu ý/Rủi ro:
Kết quả: PASS | FAIL
```

## 7) Gỡ lỗi nhanh

- Trên Windows, nếu lỗi font/emoji khi in log, đặt UTF-8 trước khi chạy:

```powershell
$env:PYTHONIOENCODING='utf-8'
```

- Nếu gặp lỗi import, kiểm tra đã cài dependencies ở mục 1.1 và script đang chạy từ root repository.
