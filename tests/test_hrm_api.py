"""Tests for HRMClient - import trực tiếp từ main_code/2024/hrm_api.py.

Chạy bằng lệnh: python tests/test_hrm_api.py
"""
import sys
import os
import time
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import tests.conftest

# ── IMPORT THẲNG TỪ CODE GỐC ────────────────────────────────────────
from custom_components.javis_hanet.hrm_api import HRMClient

# ── Mock Helpers ─────────────────────────────────────────────────────
def _mock_aiohttp_response(status=200, json_data=None, text_data=""):
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=json_data or {})
    resp.text = AsyncMock(return_value=text_data)
    return resp

def _mock_session(response):
    cm_resp = AsyncMock()
    cm_resp.__aenter__ = AsyncMock(return_value=response)
    cm_resp.__aexit__ = AsyncMock(return_value=False)
    session = AsyncMock()
    session.post = MagicMock(return_value=cm_resp)
    session.get = MagicMock(return_value=cm_resp)
    cm_session = AsyncMock()
    cm_session.__aenter__ = AsyncMock(return_value=session)
    cm_session.__aexit__ = AsyncMock(return_value=False)
    return cm_session

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
print("🧪 TEST HRM API (Import trực tiếp từ main_code/2024)")
print("=" * 60)

async def run_all_tests():
    global tests_run, tests_failed

    # ── Token Tests ──────────────────────────────────────────────────
    print("\n── Token Management ──")

    # Test 1: Get token success
    client = HRMClient()
    resp = _mock_aiohttp_response(200, {
        "statusCode": 200,
        "data": {"access_token": "abc123", "expires_in": 3600},
    })
    with patch("aiohttp.ClientSession", return_value=_mock_session(resp)):
        token = await client.get_token()
    check("get_token success", token, "abc123")
    check("access_token cached", client.access_token, "abc123")
    check_true("token_expires_at set future", client.token_expires_at > time.time())

    # Test 2: Token cached (không gọi API)
    client2 = HRMClient()
    client2.access_token = "cached_token"
    client2.token_expires_at = time.time() + 3600
    token2 = await client2.get_token()
    check("get_token cached", token2, "cached_token")

    # Test 3: Token refresh khi sắp hết hạn
    client3 = HRMClient()
    client3.access_token = "old_token"
    client3.token_expires_at = time.time() + 30  # < 60s buffer
    resp3 = _mock_aiohttp_response(200, {"data": {"access_token": "new_token", "expires_in": 3600}})
    with patch("aiohttp.ClientSession", return_value=_mock_session(resp3)):
        token3 = await client3.get_token()
    check("get_token refresh near expiry", token3, "new_token")

    # Test 4: Token API failure
    client4 = HRMClient()
    resp4 = _mock_aiohttp_response(403)
    with patch("aiohttp.ClientSession", return_value=_mock_session(resp4)):
        token4 = await client4.get_token()
    check("get_token failure -> None", token4, None)

    # Test 5: Network error
    client5 = HRMClient()
    mock_session_err = AsyncMock()
    mock_session_err.__aenter__ = AsyncMock(side_effect=Exception("Connection refused"))
    mock_session_err.__aexit__ = AsyncMock(return_value=False)
    with patch("aiohttp.ClientSession", return_value=mock_session_err):
        token5 = await client5.get_token()
    check("get_token network error -> None", token5, None)

    # ── Queue Tests ──────────────────────────────────────────────────
    print("\n── Queue Fetching ──")

    # Test 6: Fetch queue success
    client6 = HRMClient()
    client6.access_token = "valid"
    client6.token_expires_at = time.time() + 3600
    queue_items = [
        {"id": 1, "person_id": "p1", "action": "upsert", "start_time": "2026-01-01"},
        {"id": 2, "person_id": "p2", "action": "upsert"},
    ]
    resp6 = _mock_aiohttp_response(200, {"statusCode": 200, "data": queue_items})
    with patch("aiohttp.ClientSession", return_value=_mock_session(resp6)):
        result6 = await client6.fetch_queue(place_id=5390, limit=50)
    check("fetch_queue success", result6, queue_items)
    check("fetch_queue count", len(result6), 2)

    # Test 7: Fetch queue empty
    client7 = HRMClient()
    client7.access_token = "valid"
    client7.token_expires_at = time.time() + 3600
    resp7 = _mock_aiohttp_response(200, {"statusCode": 200, "data": []})
    with patch("aiohttp.ClientSession", return_value=_mock_session(resp7)):
        result7 = await client7.fetch_queue(place_id=5390)
    check("fetch_queue empty", result7, [])

    # ── ACK Tests ────────────────────────────────────────────────────
    print("\n── ACK Queue ──")

    # Test 8: ACK success
    client8 = HRMClient()
    client8.access_token = "valid"
    client8.token_expires_at = time.time() + 3600
    resp8 = _mock_aiohttp_response(200, {"statusCode": 200, "data": {"success": 2}})
    with patch("aiohttp.ClientSession", return_value=_mock_session(resp8)):
        result8 = await client8.ack_queue([{"queue_id": 1, "success": True}])
    check("ack_queue success", result8, True)

    # Test 9: ACK empty
    client9 = HRMClient()
    result9 = await client9.ack_queue([])
    check("ack_queue empty -> True", result9, True)

    # Test 10: ACK failure
    client10 = HRMClient()
    client10.access_token = "valid"
    client10.token_expires_at = time.time() + 3600
    resp10 = _mock_aiohttp_response(500, text_data="Server Error")
    with patch("aiohttp.ClientSession", return_value=_mock_session(resp10)):
        result10 = await client10.ack_queue([{"queue_id": 1, "success": True}])
    check("ack_queue failure -> False", result10, False)

# ── Chứng minh đường dẫn ──
print("\n── Chứng minh đường dẫn ──")
from custom_components.javis_hanet import hrm_api as hrm_mod
check_true("hrm_api.__file__ trỏ tới main_code/2024",
           "main_code" in hrm_mod.__file__ and "2024" in hrm_mod.__file__)
print(f"  📁 File thật: {hrm_mod.__file__}")

# Chạy async tests
asyncio.run(run_all_tests())

# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
if tests_failed == 0:
    print(f"🎉 TẤT CẢ {tests_run} TESTS ĐỀU PASS!")
else:
    print(f"💥 {tests_failed}/{tests_run} TESTS BỊ FAIL!")
print("=" * 60 + "\n")
sys.exit(0 if tests_failed == 0 else 1)
