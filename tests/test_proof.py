"""
Script chạy bằng lệnh: python tests/test_proof.py
Mục đích: Chứng minh Test đang đọc thẳng vào main_code/2024 VÀ bắt lỗi nếu code sai.
"""
import os
import sys
import traceback

# Khai báo đường dẫn để module import có thể đọc đc tests.conftest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Nạp conftest.py để kích hoạt cơ chế Alias
import tests.conftest

# Import code THẬT thông qua cái tên GIẢ
import custom_components.javis_hanet.const as javis_const
import custom_components.javis_hanet.__init__ as javis_init

# ══════════════════════════════════════════════════
# PHẦN 1: CHỨNG MINH ĐƯỜNG DẪN
# ══════════════════════════════════════════════════
expected_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../main_code/2024/__init__.py"))
actual_path = os.path.abspath(javis_init.__file__)

print("\n" + "=" * 60)
print("🔎 BẰNG CHỨNG HỆ THỐNG PYTHON 🔎")
print("=" * 60)
print(f"\n  File __init__.py đang đọc từ: {actual_path}")
print(f"  File const.py   đang đọc từ: {os.path.abspath(javis_const.__file__)}")

if actual_path == expected_path:
    print("\n  ✅ Đường dẫn ĐÚNG: Test đang chọc thẳng vào main_code/2024")
else:
    print("\n  ❌ Đường dẫn SAI!")

# ══════════════════════════════════════════════════
# PHẦN 2: KIỂM TRA GIÁ TRỊ BIẾN (BẮT LỖI CODE)
# ══════════════════════════════════════════════════
print("\n" + "=" * 60)
print("🧪 KIỂM TRA GIÁ TRỊ BIẾN TRONG CODE GỐC")
print("=" * 60)

all_passed = True
tests_run = 0
tests_failed = 0

def check(test_name, actual, expected):
    global all_passed, tests_run, tests_failed
    tests_run += 1
    if actual == expected:
        print(f"  ✅ PASS: {test_name}")
    else:
        all_passed = False
        tests_failed += 1
        print(f"  ❌ FAIL: {test_name}")
        print(f"         Mong đợi : {expected!r}")
        print(f"         Nhận được: {actual!r}")

# Test 1: DOMAIN phải đúng
check("DOMAIN == 'javis_hanet'", javis_const.DOMAIN, "javis_hanet")

# Test 2: Hàm remove_person_id phải tồn tại
check("Hàm remove_person_id_in_value_template tồn tại",
      hasattr(javis_init, "remove_person_id_in_value_template"), True)

# Test 3: Hàm async_unload_entry phải tồn tại
check("Hàm async_unload_entry tồn tại",
      hasattr(javis_init, "async_unload_entry"), True)

# Test 4: PERSON_FILE_LOCK phải tồn tại (chống Race Condition)
check("PERSON_FILE_LOCK tồn tại",
      hasattr(javis_init, "PERSON_FILE_LOCK"), True)

# Test 5: Regex xóa ID phải hoạt động đúng
if hasattr(javis_init, "remove_person_id_in_value_template"):
    template = "{% if value_json.personID in ['1', '12', '111'] %}"
    result = javis_init.remove_person_id_in_value_template(1, template)
    check("Regex xóa ID '1' không làm hỏng '12' và '111'",
          result, "{% if value_json.personID in ['12', '111'] %}")

# ══════════════════════════════════════════════════
# KẾT QUẢ TỔNG HỢP
# ══════════════════════════════════════════════════
print("\n" + "=" * 60)
if all_passed:
    print(f"🎉 TẤT CẢ {tests_run} TESTS ĐỀU PASS!")
else:
    print(f"💥 {tests_failed}/{tests_run} TESTS BỊ FAIL!")
    print("   👆 Hãy kiểm tra lại code trong main_code/2024!")
print("=" * 60 + "\n")

# Trả exit code để CI/CD có thể dùng
sys.exit(0 if all_passed else 1)
