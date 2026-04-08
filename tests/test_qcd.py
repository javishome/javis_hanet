"""Tests for QCD service + upload flow.

Run: python tests/test_qcd.py
"""

import asyncio
import os
import sys
import tempfile
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import tests.conftest

import custom_components.javis_hanet.__init__ as javis_init
import custom_components.javis_hanet.utils as javis_utils


tests_run = 0
tests_failed = 0


def show_case(case_id, goal, test_input, expected_output, note):
    print("\n" + "-" * 60)
    print(f"CASE {case_id}: {goal}")
    print(f"Input: {test_input}")
    print(f"Expected output: {expected_output}")
    print(f"Note: {note}")


def check(test_name, actual, expected):
    global tests_run, tests_failed
    tests_run += 1
    if actual == expected:
        print(f"  PASS: {test_name}")
    else:
        tests_failed += 1
        print(f"  FAIL: {test_name}")
        print(f"        Expected: {expected!r}")
        print(f"        Actual  : {actual!r}")


def check_true(test_name, condition):
    global tests_run, tests_failed
    tests_run += 1
    if condition:
        print(f"  PASS: {test_name}")
    else:
        tests_failed += 1
        print(f"  FAIL: {test_name}")


class FakeCall:
    def __init__(self, data):
        self.data = data


class FakeHass:
    def __init__(self):
        self.tasks = []

    def async_create_task(self, coro):
        task = asyncio.create_task(coro)
        self.tasks.append(task)
        return task


class _FakeResponse:
    def __init__(self, status):
        self.status = status

    async def json(self):
        return {"status": self.status}


class _FakePostCtx:
    def __init__(self, status):
        self._response = _FakeResponse(status)

    async def __aenter__(self):
        return self._response

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeSession:
    def __init__(self, status):
        self._status = status

    def post(self, *args, **kwargs):
        return _FakePostCtx(self._status)


class _FakeSessionCtx:
    def __init__(self, status):
        self._session = _FakeSession(status)

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False


print("\n" + "=" * 60)
print("TEST QCD FLOW")
print("=" * 60)


async def case_service_schedules_upload_task(secret_key):
    show_case(
        "QCD-001",
        "Service handler tạo task upload nền",
        f"secret_key={secret_key}",
        "status=ok và 1 task được tạo",
        "Giống hành vi thực tế của service push_to_qcd.",
    )

    fake_hass = FakeHass()
    svc = javis_init.Services(fake_hass)

    with patch.object(
        javis_init, "change_file_name", AsyncMock(return_value=True)
    ) as mock_change:
        result = await svc.change_face_log_name(FakeCall({"secret_key": secret_key}))
        check("QCD-001 service status", result.get("status"), "ok")
        check("QCD-001 background task count", len(fake_hass.tasks), 1)
        await asyncio.gather(*fake_hass.tasks)
        check("QCD-001 upload called", mock_change.await_count, 1)
        check("QCD-001 args", mock_change.await_args.args, (secret_key, None))


async def case_invalid_date_returns_none(secret_key):
    show_case(
        "QCD-002",
        "Date sai format bị từ chối",
        "date_str='2026/01/01'",
        "return None",
        "change_file_name chỉ nhận YYYY-MM-DD.",
    )
    result = await javis_utils.change_file_name(secret_key, "2026/01/01")
    check("QCD-002 invalid date", result, None)


async def case_live_api_with_real_secret(secret_key):
    show_case(
        "QCD-003",
        "Gọi API QCD thật",
        "secret_key thật + empty timesheet.log",
        "return True + file đổi tên thành YYMMDD.log",
        "Case này gọi endpoint thật qcd.arrow-tech.vn.",
    )

    with tempfile.TemporaryDirectory() as tmp:
        folder = tmp + os.sep
        source_file = os.path.join(tmp, "timesheet.log")
        renamed_file = os.path.join(tmp, "260101.log")

        with open(source_file, "w", encoding="utf-8") as f:
            f.write("")

        old_folder = javis_utils.FOLDER_PERSON_LOG
        old_path = javis_utils.PATH_PERSON_LOG
        try:
            javis_utils.FOLDER_PERSON_LOG = folder
            javis_utils.PATH_PERSON_LOG = source_file
            result = await javis_utils.change_file_name(secret_key, "2026-01-01")
        finally:
            javis_utils.FOLDER_PERSON_LOG = old_folder
            javis_utils.PATH_PERSON_LOG = old_path

        check("QCD-003 live api result", result, True)
        check_true("QCD-003 renamed file exists", os.path.exists(renamed_file))


async def case_non_200_returns_false(secret_key):
    show_case(
        "QCD-004",
        "API trả non-200 thì trả False",
        "mocked HTTP 500",
        "return False",
        "Xác nhận nhánh lỗi upload.",
    )

    with tempfile.TemporaryDirectory() as tmp:
        folder = tmp + os.sep
        source_file = os.path.join(tmp, "timesheet.log")
        with open(source_file, "w", encoding="utf-8") as f:
            f.write("{'person_id': 'p001'}\n")

        old_folder = javis_utils.FOLDER_PERSON_LOG
        old_path = javis_utils.PATH_PERSON_LOG
        try:
            javis_utils.FOLDER_PERSON_LOG = folder
            javis_utils.PATH_PERSON_LOG = source_file
            with patch(
                "custom_components.javis_hanet.utils.aiohttp.ClientSession",
                return_value=_FakeSessionCtx(500),
            ):
                result = await javis_utils.change_file_name(secret_key, "2026-01-01")
        finally:
            javis_utils.FOLDER_PERSON_LOG = old_folder
            javis_utils.PATH_PERSON_LOG = old_path

    check("QCD-004 mocked non-200", result, False)


async def case_missing_source_log_returns_none(secret_key):
    show_case(
        "QCD-005",
        "Không có timesheet.log thì thoát sớm",
        "date_str=None và file nguồn không tồn tại",
        "return None",
        "Nhánh an toàn khi chưa có log để đẩy QCD.",
    )

    with tempfile.TemporaryDirectory() as tmp:
        folder = tmp + os.sep
        source_file = os.path.join(tmp, "timesheet.log")

        old_folder = javis_utils.FOLDER_PERSON_LOG
        old_path = javis_utils.PATH_PERSON_LOG
        try:
            javis_utils.FOLDER_PERSON_LOG = folder
            javis_utils.PATH_PERSON_LOG = source_file
            result = await javis_utils.change_file_name(secret_key, None)
        finally:
            javis_utils.FOLDER_PERSON_LOG = old_folder
            javis_utils.PATH_PERSON_LOG = old_path

    check("QCD-005 missing source log", result, None)


async def main():
    secret_key = os.environ.get("QCD_TEST_SECRET", "zybzfmxOwv")
    await case_service_schedules_upload_task(secret_key)
    await case_invalid_date_returns_none(secret_key)
    await case_live_api_with_real_secret(secret_key)
    await case_non_200_returns_false(secret_key)
    await case_missing_source_log_returns_none(secret_key)


asyncio.run(main())

print("\n" + "=" * 60)
if tests_failed == 0:
    print(f"ALL {tests_run} TESTS PASSED")
else:
    print(f"FAILED: {tests_failed}/{tests_run}")
print("=" * 60 + "\n")

sys.exit(0 if tests_failed == 0 else 1)
