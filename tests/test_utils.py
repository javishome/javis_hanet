"""Tests for utility functions: JSON/YAML I/O, version check, URL helpers, MAC.

Cập nhật: Import trực tiếp từ main_code/2024/utils.py thay vì viết lại standalone.
Chạy bằng lệnh: python tests/test_utils.py
"""
import sys
import os
import json
import tempfile
import yaml
import traceback

# Khai báo đường dẫn để module import có thể đọc đc tests.conftest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import tests.conftest

# ── IMPORT THẲNG TỪ CODE GỐC ────────────────────────────────────────
from custom_components.javis_hanet.utils import (
    yaml2dict,
    dict2yaml,
    get_host,
    is_new_version,
)
# load_json_file và save_json_file nằm trong utils.py
# Kiểm tra xem hàm có tồn tại không, nếu không fallback
try:
    from custom_components.javis_hanet.utils import load_json_file, write_data
except ImportError:
    load_json_file = None
    write_data = None


# ── TEST RUNNER ──────────────────────────────────────────────────────
tests_run = 0
tests_failed = 0

def check(test_name, actual, expected):
    global tests_run, tests_failed
    tests_run += 1
    if actual == expected:
        print(f"  ✅ PASS: {test_name}")
    else:
        tests_failed += 1
        print(f"  ❌ FAIL: {test_name}")
        print(f"         Mong đợi : {expected!r}")
        print(f"         Nhận được: {actual!r}")

def check_true(test_name, condition):
    global tests_run, tests_failed
    tests_run += 1
    if condition:
        print(f"  ✅ PASS: {test_name}")
    else:
        tests_failed += 1
        print(f"  ❌ FAIL: {test_name}")


# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("🧪 TEST UTILS.PY (Import trực tiếp từ main_code/2024)")
print("=" * 60)

# ── YAML I/O Tests ──────────────────────────────────────────────────
print("\n── YAML I/O ──")

with tempfile.TemporaryDirectory() as tmp:
    # Test 1: Save and load YAML
    fp = os.path.join(tmp, "test.yaml")
    data = {"entities": ["light.living", "switch.fan"]}
    dict2yaml(data, fp)
    loaded = yaml2dict(fp)
    check("YAML save & load roundtrip", loaded, data)

    # Test 2: Load nonexistent creates empty file
    fp2 = os.path.join(tmp, "auto.yaml")
    result = yaml2dict(fp2)
    check("YAML load nonexistent -> None", result, None)
    check_true("YAML load nonexistent creates file", os.path.exists(fp2))

    # Test 3: Unicode YAML
    fp3 = os.path.join(tmp, "vn.yaml")
    data3 = {"tên": "Nguyễn Văn A"}
    dict2yaml(data3, fp3)
    loaded3 = yaml2dict(fp3)
    check("YAML Unicode roundtrip", loaded3["tên"], "Nguyễn Văn A")

# ── URL Helper Tests ─────────────────────────────────────────────────
print("\n── URL Helpers (get_host) ──")

# get_host trong code gốc (utils.py) KHÔNG nhận tham số mode/server_url
# nó dùng biến toàn cục MODE và SERVER_URL từ const.py
# Nên ta test bằng cách gọi trực tiếp và kiểm tra output
from custom_components.javis_hanet.const import MODE, SERVER_URL
if MODE not in ("dev", "dev_ha_real"):
    result = get_host("javisco.com")
    check("get_host('javisco.com') chứa đúng URL", "javisco.com" in result, True)
    check("get_host('javisco.com') bắt đầu từ SERVER_URL", result.startswith(SERVER_URL), True)
else:
    result = get_host("javisco.com")
    check("get_host dev mode trả SERVER_URL", result, SERVER_URL)

# ── Version Check Tests ─────────────────────────────────────────────
print("\n── Version Check (is_new_version) ──")

# is_new_version() trong code gốc KHÔNG nhận tham số, nó đọc __version__ từ HA
# Ta chỉ kiểm tra nó có chạy được mà không crash
check_true("is_new_version() chạy không crash", isinstance(is_new_version(), bool))

# ── Chứng minh đang import code gốc ─────────────────────────────────
print("\n── Chứng minh đường dẫn ──")
import custom_components.javis_hanet.utils as utils_mod
check_true("utils.__file__ trỏ tới main_code/2024/utils.py",
           "main_code" in utils_mod.__file__ and "2024" in utils_mod.__file__)
print(f"  📁 File thật: {utils_mod.__file__}")

# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
if tests_failed == 0:
    print(f"🎉 TẤT CẢ {tests_run} TESTS ĐỀU PASS!")
else:
    print(f"💥 {tests_failed}/{tests_run} TESTS BỊ FAIL!")
print("=" * 60 + "\n")
sys.exit(0 if tests_failed == 0 else 1)
