"""Script tests for Services.update_period handler.

Run: python tests/test_service_update_period.py
"""

import asyncio
import copy
import os
import sys
from datetime import date
from unittest.mock import AsyncMock, patch

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


class FakeCall:
    def __init__(self, data):
        self.data = data


class FakeHass:
    def __init__(self):
        self.executor_jobs = []

    async def async_add_executor_job(self, func, *args):
        self.executor_jobs.append((getattr(func, "__name__", str(func)), args))
        return func(*args)


async def run_case(initial_data, call_data):
    storage = {"data": copy.deepcopy(initial_data), "saved": None}

    def fake_load(_path):
        return storage["data"]

    def fake_save(_path, data):
        storage["saved"] = copy.deepcopy(data)

    update_api_mock = AsyncMock(return_value=None)
    remove_expired_mock = AsyncMock(return_value=None)
    restart_mqtt_mock = AsyncMock(return_value=None)

    hass = FakeHass()
    services = javis_init.Services(hass)

    with (
        patch.object(javis_init, "load_json_file", side_effect=fake_load),
        patch.object(javis_init, "save_json_file", side_effect=fake_save),
        patch.object(javis_init, "update_period_api", update_api_mock),
        patch.object(
            javis_init, "remove_expired_pids_from_face_sensor", remove_expired_mock
        ),
        patch.object(javis_init, "restart_mqtt", restart_mqtt_mock),
    ):
        result = await services.update_period(FakeCall(call_data))

    return {
        "result": result,
        "storage": storage,
        "update_api_mock": update_api_mock,
        "remove_expired_mock": remove_expired_mock,
        "restart_mqtt_mock": restart_mqtt_mock,
        "hass": hass,
    }


print("\n" + "=" * 60)
print("TEST SERVICE UPDATE_PERIOD")
print("=" * 60)


async def main():
    show_case(
        "UP-001",
        "Update existing person with non-expired end_time",
        "person_id='p001', start_time=2026-01-01, end_time=2999-01-01",
        "status=ok, JSON updated, API called once, no sensor removal",
        "Future end_time should skip expiration branch.",
    )
    case1 = await run_case(
        {
            "person": [
                {
                    "person_id": "p001",
                    "person_name": "Person 1",
                    "start_time": "",
                    "end_time": "",
                }
            ]
        },
        {
            "person_id": "p001",
            "start_time": date(2026, 1, 1),
            "end_time": date(2999, 1, 1),
        },
    )

    check("UP-001 returns ok", case1["result"]["status"], "ok")
    check(
        "UP-001 saves start_time",
        case1["storage"]["saved"]["person"][0]["start_time"],
        "2026-01-01",
    )
    check(
        "UP-001 saves end_time",
        case1["storage"]["saved"]["person"][0]["end_time"],
        "2999-01-01",
    )
    check(
        "UP-001 update_period_api called once", case1["update_api_mock"].await_count, 1
    )
    check(
        "UP-001 remove expired not called", case1["remove_expired_mock"].await_count, 0
    )
    check("UP-001 restart MQTT not called", case1["restart_mqtt_mock"].await_count, 0)
    check(
        "UP-001 API args",
        case1["update_api_mock"].await_args.args,
        ("2026-01-01", "2999-01-01", "p001"),
    )

    show_case(
        "UP-002",
        "Reject unknown person_id",
        "person_id='not_found'",
        "status=error, no save, API not called",
        "Should return early when local person does not exist.",
    )
    case2 = await run_case(
        {"person": [{"person_id": "p001", "person_name": "Person 1"}]},
        {
            "person_id": "not_found",
            "start_time": date(2026, 1, 1),
            "end_time": date(2026, 12, 31),
        },
    )

    check("UP-002 returns error", case2["result"]["status"], "error")
    check_true(
        "UP-002 message mentions missing person",
        "not found" in case2["result"]["message"].lower(),
    )
    check("UP-002 does not save", case2["storage"]["saved"], None)
    check("UP-002 API not called", case2["update_api_mock"].await_count, 0)

    show_case(
        "UP-003",
        "Expired end_time triggers cleanup path",
        "person_id='p001', end_time=2000-01-01",
        "status=ok, remove_expired called, restart_mqtt called",
        "Past end_time should enter expiration branch reliably.",
    )
    case3 = await run_case(
        {
            "person": [
                {
                    "person_id": "p001",
                    "person_name": "Person 1",
                    "start_time": "",
                    "end_time": "",
                }
            ]
        },
        {
            "person_id": "p001",
            "start_time": date(2026, 1, 1),
            "end_time": date(2000, 1, 1),
        },
    )

    check("UP-003 returns ok", case3["result"]["status"], "ok")
    check(
        "UP-003 remove expired called once", case3["remove_expired_mock"].await_count, 1
    )
    check("UP-003 restart MQTT called once", case3["restart_mqtt_mock"].await_count, 1)
    check("UP-003 API still called", case3["update_api_mock"].await_count, 1)
    check(
        "UP-003 remove args",
        case3["remove_expired_mock"].await_args.args[0],
        ["p001"],
    )
    check_true(
        "UP-003 remove uses current hass instance",
        case3["remove_expired_mock"].await_args.args[1] is case3["hass"],
    )


asyncio.run(main())

print("\n" + "=" * 60)
if tests_failed == 0:
    print(f"ALL {tests_run} TESTS PASSED")
else:
    print(f"FAILED: {tests_failed}/{tests_run}")
print("=" * 60 + "\n")

sys.exit(0 if tests_failed == 0 else 1)
