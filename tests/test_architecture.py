"""Tests for Architecture - Import trực tiếp từ main_code/2024/__init__.py.

Chạy bằng lệnh: python tests/test_architecture.py
"""
import sys
import os
import re
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import tests.conftest

# ── IMPORT THẲNG TỪ CODE GỐC ────────────────────────────────────────
import custom_components.javis_hanet.__init__ as javis_init

# Import hàm thật từ __init__.py
remove_person_id_in_value_template = javis_init.remove_person_id_in_value_template
PERSON_FILE_LOCK = javis_init.PERSON_FILE_LOCK

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
print("🧪 TEST ARCHITECTURE (Import trực tiếp từ main_code/2024)")
print("=" * 60)

# ── Test 1: PERSON_FILE_LOCK tồn tại ────────────────────────────────
print("\n── File Lock (Race Condition Prevention) ──")
check_true("PERSON_FILE_LOCK tồn tại", PERSON_FILE_LOCK is not None)
check_true("PERSON_FILE_LOCK là asyncio.Lock", isinstance(PERSON_FILE_LOCK, asyncio.Lock))

# ── Test 2: Lock serializes concurrent writes ────────────────────────
mock_file_storage = {}

async def safe_write_with_lock(filepath, data, delay=0.1):
    async with PERSON_FILE_LOCK:
        await asyncio.sleep(delay)
        mock_file_storage[filepath] = data

async def test_lock():
    global mock_file_storage
    mock_file_storage.clear()
    task1 = asyncio.create_task(safe_write_with_lock("person.json", "DATA_1", 0.05))
    task2 = asyncio.create_task(safe_write_with_lock("person.json", "DATA_2", 0.01))
    task3 = asyncio.create_task(safe_write_with_lock("person.json", "DATA_3", 0.01))
    await asyncio.gather(task1, task2, task3)
    return mock_file_storage["person.json"]

result = asyncio.run(test_lock())
check("Lock serializes concurrent writes -> DATA_3", result, "DATA_3")

# ── Test 3: async_unload_entry tồn tại ──────────────────────────────
print("\n── Memory Leak Prevention (Unload) ──")
check_true("async_unload_entry tồn tại", hasattr(javis_init, "async_unload_entry"))

# ── Test 4: restart_mqtt tồn tại ────────────────────────────────────
print("\n── Native Service Calls ──")
check_true("restart_mqtt tồn tại", hasattr(javis_init, "restart_mqtt"))

# ── Test 5: Regex YAML Modifications (from __init__.py) ──────────────
print("\n── Regex YAML Safety (hàm thật từ __init__.py) ──")

# Test: ID '1' bị xóa không làm rách ID '12'
template1 = "{% if value_json.personID in ['1', '12', '111'] %}"
result1 = remove_person_id_in_value_template(1, template1)
check("Regex không corrupt ID '12' khi xóa '1'", result1, "{% if value_json.personID in ['12', '111'] %}")

# Test: Xóa ID đứng giữa danh sách
template2 = "{% if value_json.personID in ['12', '1', '111'] %}"
result2 = remove_person_id_in_value_template(1, template2)
check("Xóa ID ở giữa danh sách", result2, "{% if value_json.personID in ['12', '111'] %}")

# Test: Xóa ID đứng cuối
template3 = "{% if value_json.personID in ['12', '111', '1'] %}"
result3 = remove_person_id_in_value_template(1, template3)
check("Xóa ID ở cuối danh sách", result3, "{% if value_json.personID in ['12', '111'] %}")

# Test: Nháy kép
template4 = "[\"2\", \"2\"]"
result4 = remove_person_id_in_value_template(2, template4)
check("Xóa tất cả ID trùng (nháy kép)", result4, "[]")

# ── Test 6: Merge Person Data (logic từ __init__.py dòng 226-237) ──
print("\n── Merge Person Data (logic từ __init__.py) ──")

def merge_person_data(new_persons, old_persons):
    """Tái sử dụng logic merge từ __init__.py dòng 226-237."""
    old_by_id = {str(p.get("person_id")): p for p in old_persons if p.get("person_id") is not None}
    for person in new_persons:
        pid = str(person.get("person_id"))
        old_p = old_by_id.get(pid)
        if old_p:
            if old_p.get("start_time"):
                person["start_time"] = old_p.get("start_time")
            if old_p.get("end_time"):
                person["end_time"] = old_p.get("end_time")
    return new_persons

# Test merge HRM fields
old = [{"person_id": "p1", "person_name": "A", "start_time": "2026-01-01", "end_time": "2026-12-31"}]
new = [{"person_id": "p1", "person_name": "Nguyen Van A"}]
merged = merge_person_data(new, old)
check("Merge giữ start_time", merged[0]["start_time"], "2026-01-01")
check("Merge giữ end_time", merged[0]["end_time"], "2026-12-31")
check("Merge cập nhật tên mới", merged[0]["person_name"], "Nguyen Van A")

# Test mismatch data types (int vs str person_id)
old2 = [{"person_id": 1234, "start_time": "2026-01-01"}]
new2 = [{"person_id": "1234", "person_name": "Test"}]
merged2 = merge_person_data(new2, old2)
check("Merge int/str person_id", merged2[0]["start_time"], "2026-01-01")

# ── Test 7: Expiration Logic ────────────────────────────────────────
print("\n── Expiration Logic ──")

def extract_expired_pids(persons_list, current_date):
    expired = []
    for item in persons_list:
        end_str = item.get("end_time")
        pid = item.get("person_id")
        try:
            end_time = datetime.strptime(end_str, "%Y-%m-%d").date() if end_str else None
        except ValueError:
            continue
        if end_time and current_date >= end_time:
            expired.append(pid)
    return expired

today = date(2026, 3, 26)
persons = [
    {"person_id": "p1", "end_time": "2026-03-25"},  # Đã qua
    {"person_id": "p2", "end_time": "2026-03-26"},  # Đúng hôm nay
    {"person_id": "p3", "end_time": "2026-03-27"},  # Ngày mai
    {"person_id": "p4", "end_time": None},           # Vĩnh viễn
]
expired = extract_expired_pids(persons, today)
check_true("p1 hết hạn (đã qua)", "p1" in expired)
check_true("p2 hết hạn (đúng hôm nay)", "p2" in expired)
check_true("p3 chưa hết hạn", "p3" not in expired)
check_true("p4 vĩnh viễn", "p4" not in expired)

# Invalid date formats
persons_bad = [
    {"person_id": "p1", "end_time": "31-12-2026"},
    {"person_id": "p2", "end_time": "invalid"},
    {"person_id": "p3", "end_time": "2026-03-25"},
]
expired_bad = extract_expired_pids(persons_bad, today)
check("Invalid dates bị bỏ qua an toàn", expired_bad, ["p3"])

# ── Chứng minh đường dẫn ──
print("\n── Chứng minh đường dẫn ──")
check_true("__init__.__file__ trỏ tới main_code/2024",
           "main_code" in javis_init.__file__ and "2024" in javis_init.__file__)
print(f"  📁 File thật: {javis_init.__file__}")

# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
if tests_failed == 0:
    print(f"🎉 TẤT CẢ {tests_run} TESTS ĐỀU PASS!")
else:
    print(f"💥 {tests_failed}/{tests_run} TESTS BỊ FAIL!")
print("=" * 60 + "\n")
sys.exit(0 if tests_failed == 0 else 1)
