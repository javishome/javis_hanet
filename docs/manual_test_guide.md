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
python tests/test_qcd.py
```

Nếu muốn đặt `secret_key` theo môi trường khi chạy test QCD:

```bash
# Linux/macOS
QCD_TEST_SECRET=zybzfmxOwv python tests/test_qcd.py
```

```bat
:: Windows CMD
set QCD_TEST_SECRET=zybzfmxOwv
python tests/test_qcd.py
```

```powershell
# Windows PowerShell
$env:QCD_TEST_SECRET = "zybzfmxOwv"
python tests/test_qcd.py
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
  - **HC-004**
    - Đầu vào: đăng ký daily cleanup scheduler
    - Đầu ra mong đợi: callback được lên lịch lúc `00:05:00` và gọi cleanup
    - Lưu ý: chạy độc lập, không phụ thuộc `hrm_sync_enabled`
  - **HC-005**
    - Đầu vào: unload entry khi đã có listeners
    - Đầu ra mong đợi: hủy cả `hrm_sync_listener` và `daily_cleanup_listener`
    - Lưu ý: tránh nhân đôi listener sau reload

- `tests/test_qcd.py`
  - **QCD-001**
    - Đầu vào: gọi service handler `push_to_qcd` với `secret_key`
    - Đầu ra mong đợi: `status=ok`, tạo background task gửi QCD
    - Lưu ý: service trả kết quả ngay, upload chạy nền
  - **QCD-002**
    - Đầu vào: `date` sai định dạng (không phải YYYY-MM-DD)
    - Đầu ra mong đợi: hàm xử lý trả `None`, không gọi API
    - Lưu ý: kiểm tra validate ngày
  - **QCD-003**
    - Đầu vào: gọi API QCD thật với `secret_key` test
    - Đầu ra mong đợi: trả `True` khi API phản hồi 200
    - Lưu ý: cần có internet và endpoint QCD sẵn sàng
  - **QCD-004**
    - Đầu vào: API QCD trả non-200 (mock)
    - Đầu ra mong đợi: trả `False`
    - Lưu ý: xác nhận nhánh lỗi upload
  - **QCD-005**
    - Đầu vào: không có file `timesheet.log`
    - Đầu ra mong đợi: trả `None`
    - Lưu ý: xác nhận nhánh thoát sớm an toàn

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

### 5.1 Checklist bắt buộc trên giao diện Home Assistant

> Mục này là **danh sách tối thiểu bắt buộc** phải chạy trên UI Home Assistant trước khi nghiệm thu.

#### Nhóm A - Setup / Cấu hình

##### UI-SETUP-001 Cài integration từ giao diện
- Đầu vào/Điều kiện:
  - Home Assistant đang chạy ổn định
  - Đã copy custom component vào đúng thư mục
- Bước thực hiện:
  1. Vào **Settings -> Devices & Services**
  2. Chọn **Add Integration**
  3. Tìm `Javis Hanet` và bắt đầu flow
- Đầu ra mong đợi:
  - Integration hiển thị được trong danh sách
  - Không có lỗi không tìm thấy integration
- Lưu ý:
  - Chụp màn hình trang Add Integration

##### UI-SETUP-002 Setup account type = Hanet
- Đầu vào/Điều kiện:
  - Có tài khoản Hanet hợp lệ
- Bước thực hiện:
  1. Chọn loại tài khoản `hanet`
  2. Hoàn tất OAuth
  3. Chọn place cần đồng bộ
- Đầu ra mong đợi:
  - Tạo entry thành công
  - Dữ liệu person/place được tải về file local
- Lưu ý:
  - Nếu OAuth lỗi phải có thông báo rõ nguyên nhân

##### UI-SETUP-003 Setup account type = AI Box
- Đầu vào/Điều kiện:
  - Có `ip`, `port`, `key` AI Box hợp lệ
- Bước thực hiện:
  1. Chọn loại tài khoản `ai_box`
  2. Nhập thông số AI Box
  3. Bấm lưu
- Đầu ra mong đợi:
  - Tạo entry thành công
  - Lấy được danh sách profile từ AI Box
- Lưu ý:
  - Test thêm case key sai để xác nhận nhánh lỗi `cannot_connect`

##### UI-SETUP-004 Options flow sau khi cài đặt
- Đầu vào/Điều kiện:
  - Entry đã tạo thành công
- Bước thực hiện:
  1. Mở **Configure** của integration
  2. Thay đổi tùy chọn HRM sync
  3. Lưu và mở lại để kiểm tra giá trị
- Đầu ra mong đợi:
  - Option được lưu đúng
  - Các thay đổi có hiệu lực ngay
- Lưu ý:
  - `hrm_sync_interval` phải >= 5

#### Nhóm B - Test toàn bộ service trên UI (Developer Tools)

##### UI-SVC-001 `javis_hanet.write_person`
- Đầu vào/Điều kiện:
  - Có payload JSON hợp lệ
- Bước thực hiện:
  1. Vào **Developer Tools -> Services**
  2. Chọn `javis_hanet.write_person`
  3. Gửi payload mẫu
- Đầu ra mong đợi:
  - Service trả `status: ok`
  - `timesheet.log` có thêm dòng mới
- Lưu ý:
  - Test thêm case payload JSON sai định dạng

##### UI-SVC-002 `javis_hanet.push_to_qcd`
- Đầu vào/Điều kiện:
  - Có `/config/timesheet/timesheet.log`
  - Có secret key QCD hợp lệ
- Bước thực hiện:
  1. Chọn service `javis_hanet.push_to_qcd`
  2. Nhập `secret_key` (và `date` nếu cần)
  3. Call service
- Đầu ra mong đợi:
  - Response service `status: ok`
  - File log đổi tên theo định dạng `YYMMDD.log`
  - Có log upload QCD thành công
- Lưu ý:
  - Service chạy nền, cần kiểm tra log backend để kết luận pass/fail

##### UI-SVC-003 `javis_hanet.update_period`
- Đầu vào/Điều kiện:
  - `person_id` tồn tại trong file local
- Bước thực hiện:
  1. Chọn service `javis_hanet.update_period`
  2. Nhập `person_id`, `start_time`, `end_time`
  3. Call service
- Đầu ra mong đợi:
  - Service trả `status: ok`
  - Dữ liệu period local được cập nhật
  - Có call API cập nhật period lên HRM
- Lưu ý:
  - Test thêm case `person_id` không tồn tại -> `status: error`

##### UI-SVC-004 `javis_hanet.check_faceid_group_sensor`
- Đầu vào/Điều kiện:
  - Có ít nhất 1 person đã hết hạn
- Bước thực hiện:
  1. Chọn service `javis_hanet.check_faceid_group_sensor`
  2. Call service
  3. Kiểm tra `face_sensor.yaml`
- Đầu ra mong đợi:
  - `person_id` hết hạn bị loại khỏi `value_template`
  - MQTT được reload thành công
- Lưu ý:
  - Kiểm tra không xóa nhầm ID gần giống

##### UI-SVC-005 `javis_hanet.sync_periods`
- Đầu vào/Điều kiện:
  - File local có person hợp lệ
- Bước thực hiện:
  1. Chọn service `javis_hanet.sync_periods`
  2. Call service
  3. Kiểm tra log request/response
- Đầu ra mong đợi:
  - HTTP 200 -> `status: ok`
  - HTTP lỗi -> `status: error`
- Lưu ý:
  - Record không có `person_id` phải bị bỏ qua

##### UI-SVC-006 `javis_hanet.set_hrm_sync_interval`
- Đầu vào/Điều kiện:
  - Integration đang hoạt động
- Bước thực hiện:
  1. Chọn service `javis_hanet.set_hrm_sync_interval`
  2. Nhập `interval` (ví dụ 30 hoặc 60)
  3. Call service
- Đầu ra mong đợi:
  - Service trả `status: ok`
  - Chu kỳ polling HRM thay đổi theo giá trị mới
- Lưu ý:
  - Test thêm case `interval < 5` -> phải trả lỗi

##### UI-SVC-007 `javis_hanet.set_hrm_sync_enabled`
- Đầu vào/Điều kiện:
  - Integration đang hoạt động
- Bước thực hiện:
  1. Chọn service `javis_hanet.set_hrm_sync_enabled`
  2. Gửi `enabled: true` rồi `enabled: false`
- Đầu ra mong đợi:
  - Bật/tắt HRM auto-sync ngay lập tức
  - Log vòng sync phản ánh đúng trạng thái
- Lưu ý:
  - Cần kiểm tra cả 2 chiều bật và tắt

##### UI-SVC-008 `javis_hanet.set_hrm_sync_log_enabled`
- Đầu vào/Điều kiện:
  - Integration đang hoạt động
- Bước thực hiện:
  1. Chọn service `javis_hanet.set_hrm_sync_log_enabled`
  2. Gửi `enabled: true` rồi `enabled: false`
- Đầu ra mong đợi:
  - Log debug HRM sync bật/tắt đúng theo cấu hình
- Lưu ý:
  - Khi `false`, hệ thống vẫn chạy nhưng giảm log chi tiết

#### Nhóm C - Hậu kiểm sau service

##### UI-VERIFY-001 Restart Home Assistant
- Đầu vào/Điều kiện:
  - Đã chạy qua ít nhất 1 vòng setup và service
- Bước thực hiện:
  1. Restart Home Assistant
  2. Kiểm tra lại trạng thái integration và service
- Đầu ra mong đợi:
  - Integration lên lại bình thường
  - Các option đã cấu hình vẫn được giữ
- Lưu ý:
  - Chụp log thời điểm startup để đối chiếu

##### UI-VERIFY-002 Đối soát dữ liệu file sau test
- Đầu vào/Điều kiện:
  - Đã chạy các service liên quan dữ liệu
- Bước thực hiện:
  1. Đối chiếu trước/sau của `person_javis_v2.json`
  2. Đối chiếu trước/sau của `/config/timesheet/`
  3. Đối chiếu trước/sau của `face_sensor.yaml`
- Đầu ra mong đợi:
  - Dữ liệu thay đổi đúng theo từng service
  - Không có thay đổi ngoài mong muốn
- Lưu ý:
  - Bắt buộc lưu evidence (file diff, log, ảnh màn hình)

##### UI-VERIFY-003 Tự động dọn hết hạn lúc 00:05 (không phụ thuộc HRM)
- Đầu vào/Điều kiện:
  - Có ít nhất 1 person đã hết hạn trong `person_javis_v2.json`
  - `hrm_sync_enabled` đặt `false`
- Bước thực hiện:
  1. Đảm bảo person hết hạn còn nằm trong `face_sensor.yaml`
  2. Chờ qua mốc `00:05` (giờ Hà Nội)
  3. Kiểm tra `face_sensor.yaml` và log HA
- Đầu ra mong đợi:
  - Person hết hạn bị xóa khỏi `face_sensor.yaml`
  - MQTT chỉ reload khi có thay đổi thật
- Lưu ý:
  - Không cần bật HRM sync, cơ chế dọn chạy theo lịch ngày cố định

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

### M-008 Service `push_to_qcd`
- Đầu vào/Điều kiện:
  - Có file `/config/timesheet/timesheet.log`
  - Có `secret_key` hợp lệ của QCD
- Bước thực hiện:
  1. Vào **Developer Tools -> Services**
  2. Chọn service `javis_hanet.push_to_qcd`
  3. Điền payload:

```yaml
secret_key: "zybzfmxOwv"
# date: "2026-01-01"   # optional
```

  4. Bấm **Call Service**
  5. Theo dõi log HA và thư mục `/config/timesheet/`
- Đầu ra mong đợi:
  - Service trả `status: ok`
  - File log được đổi tên theo ngày (`YYMMDD.log`)
  - API QCD nhận dữ liệu thành công (HTTP 200)
- Lưu ý:
  - Service chạy nền, cần kiểm tra log để xác nhận upload hoàn tất

#### M-008A QCD thành công (happy path)
- Đầu vào/Điều kiện:
  - `timesheet.log` có ít nhất 1 dòng dữ liệu hợp lệ
  - `secret_key` đúng
- Bước thực hiện:
  1. Gọi service như payload mẫu phía trên
  2. Mở log HA kiểm tra kết quả upload
- Đầu ra mong đợi:
  - Có log thành công gửi QCD
  - File được đổi tên đúng ngày
- Lưu ý:
  - So sánh số dòng trong file trước/sau để chắc dữ liệu đã lấy đúng nguồn

#### M-008B QCD thất bại do secret key sai
- Đầu vào/Điều kiện:
  - `timesheet.log` tồn tại
  - dùng `secret_key` sai
- Bước thực hiện:
  1. Gọi service với payload:

```yaml
secret_key: "wrong_key"
```

  2. Kiểm tra log HA
- Đầu ra mong đợi:
  - Service vẫn trả `status: ok` (do chạy nền)
  - Log backend báo lỗi upload QCD (HTTP != 200 hoặc message lỗi)
- Lưu ý:
  - Không đánh giá pass/fail chỉ dựa vào response service, phải đọc log backend

#### M-008C Không có file log nguồn
- Đầu vào/Điều kiện:
  - Không có `/config/timesheet/timesheet.log`
- Bước thực hiện:
  1. Gọi service `javis_hanet.push_to_qcd` với `secret_key` hợp lệ
- Đầu ra mong đợi:
  - Không crash integration
  - Không có request upload QCD
- Lưu ý:
  - Đây là nhánh thoát sớm; cần chụp log để xác nhận hệ thống xử lý an toàn

#### M-008D Sai định dạng `date`
- Đầu vào/Điều kiện:
  - Có file `timesheet.log`
- Bước thực hiện:
  1. Gọi service với payload:

```yaml
secret_key: "zybzfmxOwv"
date: "2026/01/01"
```

  2. Kiểm tra log HA
- Đầu ra mong đợi:
  - Có log báo lỗi định dạng ngày
  - Không upload dữ liệu lên QCD
- Lưu ý:
  - Date đúng chuẩn phải là `YYYY-MM-DD`

#### Evidence bắt buộc cho M-008
- Payload đã gửi trong Developer Tools
- Log HA trước/sau khi gọi service
- Danh sách file trong `/config/timesheet/` trước/sau (để thấy `timesheet.log -> YYMMDD.log`)
- Nếu lỗi: chụp nguyên response body từ QCD (nếu có trong log)

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

- Nếu test QCD thật bị lỗi resolver DNS trên Windows (`Channel.getaddrinfo...`), thử gỡ resolver phụ:

```bat
pip uninstall -y aiodns pycares
python tests/test_qcd.py
```

- Nếu dùng Windows CMD, không chạy được cú pháp `QCD_TEST_SECRET=... python ...`; hãy dùng:

```bat
set QCD_TEST_SECRET=zybzfmxOwv
python tests/test_qcd.py
```
