"""Script tests for sync_periods_api payload and status handling.

Run: python tests/test_sync_periods_api.py
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import tests.conftest

import custom_components.javis_hanet.__init__ as javis_init


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


class FakeHass:
    async def async_add_executor_job(self, func, *args):
        return func(*args)


def make_client_session(status_code):
    response = AsyncMock()
    response.status = status_code

    cm_response = AsyncMock()
    cm_response.__aenter__ = AsyncMock(return_value=response)
    cm_response.__aexit__ = AsyncMock(return_value=False)

    session = AsyncMock()
    session.post = MagicMock(return_value=cm_response)

    cm_session = AsyncMock()
    cm_session.__aenter__ = AsyncMock(return_value=session)
    cm_session.__aexit__ = AsyncMock(return_value=False)
    return cm_session, session


print("\n" + "=" * 60)
print("TEST SYNC_PERIODS_API")
print("=" * 60)


async def main():
    show_case(
        "SP-001",
        "Build payload and return True on HTTP 200",
        "person list with and without person_id",
        "result=True and payload includes only person_id entries",
        "Rows missing person_id must be filtered out.",
    )
    person_data_1 = {
        "person": [
            {"person_id": "p001", "start_time": "2026-01-01", "end_time": "2026-12-31"},
            {"person_id": "", "start_time": "2026-01-01", "end_time": "2026-12-31"},
            {"person_id": "p003", "start_time": None, "end_time": None},
        ]
    }
    cm_session_1, session_1 = make_client_session(200)

    with (
        patch.object(javis_init, "load_json_file", return_value=person_data_1),
        patch(
            "custom_components.javis_hanet.__init__.aiohttp.ClientSession",
            return_value=cm_session_1,
        ),
    ):
        result_1 = await javis_init.sync_periods_api(FakeHass())

    check("SP-001 returns True", result_1, True)
    check_true("SP-001 POST called", session_1.post.call_count == 1)

    post_kwargs_1 = session_1.post.call_args.kwargs
    check(
        "SP-001 payload rows",
        post_kwargs_1["json"],
        [
            {"person_id": "p001", "start_time": "2026-01-01", "end_time": "2026-12-31"},
            {"person_id": "p003", "start_time": None, "end_time": None},
        ],
    )
    check_true(
        "SP-001 includes timesheet_secret_key header",
        "timesheet_secret_key" in post_kwargs_1["headers"],
    )

    show_case(
        "SP-002",
        "Return False on non-200 response",
        "HTTP status 500",
        "result=False",
        "Failure branch should be explicit for caller service.",
    )
    person_data_2 = {
        "person": [{"person_id": "p001", "start_time": "", "end_time": ""}]
    }
    cm_session_2, session_2 = make_client_session(500)

    with (
        patch.object(javis_init, "load_json_file", return_value=person_data_2),
        patch(
            "custom_components.javis_hanet.__init__.aiohttp.ClientSession",
            return_value=cm_session_2,
        ),
    ):
        result_2 = await javis_init.sync_periods_api(FakeHass())

    check("SP-002 returns False", result_2, False)
    check_true("SP-002 POST still called", session_2.post.call_count == 1)


asyncio.run(main())

print("\n" + "=" * 60)
if tests_failed == 0:
    print(f"ALL {tests_run} TESTS PASSED")
else:
    print(f"FAILED: {tests_failed}/{tests_run}")
print("=" * 60 + "\n")

sys.exit(0 if tests_failed == 0 else 1)
