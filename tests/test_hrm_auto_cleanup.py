"""Script tests for HRM auto-sync expiration cleanup behavior.

Run: python tests/test_hrm_auto_cleanup.py
"""

import asyncio
import os
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import tests.conftest

import custom_components.javis_hanet.__init__ as javis_init
from custom_components.javis_hanet.const import DOMAIN


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


class FakeServices:
    async def async_call(self, domain, service):
        return {"domain": domain, "service": service}


class FakeHass:
    def __init__(self):
        self.data = {DOMAIN: {}}
        self.services = FakeServices()

    async def async_add_executor_job(self, func, *args):
        return func(*args)


def make_entry(enabled=True, interval=30):
    return SimpleNamespace(
        options={
            "hrm_sync_enabled": enabled,
            "hrm_sync_log_enabled": False,
            "hrm_sync_interval": interval,
        }
    )


print("\n" + "=" * 60)
print("TEST HRM AUTO-SYNC CLEANUP")
print("=" * 60)


async def case_sync_calls_cleanup_without_places():
    show_case(
        "HC-001",
        "Cleanup still runs when there is no place_id",
        "hrm_sync_enabled=true, person data has no place_id",
        "handle_person_data is called once",
        "Validates option 1: cleanup every sync cycle even if queue sync is skipped.",
    )

    hass = FakeHass()
    entry = make_entry()
    captured = {"callback": None}

    def fake_track_time_interval(_hass, callback, _delta):
        captured["callback"] = callback
        return lambda: None

    with (
        patch.object(
            javis_init,
            "async_track_time_interval",
            side_effect=fake_track_time_interval,
        ),
        patch.object(
            javis_init,
            "load_json_file",
            return_value={"person": [{"person_id": "p001", "end_time": "2000-01-01"}]},
        ),
        patch.object(
            javis_init, "handle_person_data", AsyncMock(return_value=True)
        ) as cleanup_mock,
    ):
        await javis_init.setup_hrm_sync(hass, entry)
        await captured["callback"](None)

    check_true("HC-001 callback captured", captured["callback"] is not None)
    check("HC-001 cleanup called", cleanup_mock.await_count, 1)


async def case_sync_calls_cleanup_when_queue_empty():
    show_case(
        "HC-002",
        "Cleanup still runs when HRM queue is empty",
        "hrm_sync_enabled=true, place_id exists, fetch_queue returns []",
        "handle_person_data called, ack_queue not called",
        "Queue-empty cycle must still evaluate expired users.",
    )

    hass = FakeHass()
    entry = make_entry()
    captured = {"callback": None}

    fake_client = SimpleNamespace(
        fetch_queue=AsyncMock(return_value=[]),
        ack_queue=AsyncMock(return_value=None),
    )
    hass.data[DOMAIN]["hrm_client"] = fake_client

    def fake_track_time_interval(_hass, callback, _delta):
        captured["callback"] = callback
        return lambda: None

    with (
        patch.object(
            javis_init,
            "async_track_time_interval",
            side_effect=fake_track_time_interval,
        ),
        patch.object(
            javis_init,
            "load_json_file",
            return_value={"person": [{"person_id": "p001", "place_id": 5390}]},
        ),
        patch.object(
            javis_init, "handle_person_data", AsyncMock(return_value=False)
        ) as cleanup_mock,
    ):
        await javis_init.setup_hrm_sync(hass, entry)
        await captured["callback"](None)

    check_true("HC-002 callback captured", captured["callback"] is not None)
    check("HC-002 fetch_queue called", fake_client.fetch_queue.await_count, 1)
    check("HC-002 ack_queue not called", fake_client.ack_queue.await_count, 0)
    check("HC-002 cleanup called", cleanup_mock.await_count, 1)


async def case_handle_person_data_reload_only_when_changed():
    show_case(
        "HC-003",
        "handle_person_data reloads MQTT only when sensor changed",
        "expired person list + cleanup returns True/False",
        "restart_mqtt called only on changed=True",
        "Prevents unnecessary MQTT reloads on every cycle.",
    )

    hass = FakeHass()

    with (
        patch.object(javis_init.os.path, "exists", return_value=True),
        patch.object(
            javis_init,
            "load_json_file",
            return_value={"person": [{"person_id": "p001", "end_time": "2000-01-01"}]},
        ),
        patch.object(
            javis_init,
            "remove_expired_pids_from_face_sensor",
            AsyncMock(return_value=True),
        ) as remove_mock,
        patch.object(
            javis_init, "restart_mqtt", AsyncMock(return_value=None)
        ) as mqtt_mock,
    ):
        updated_true = await javis_init.handle_person_data(hass)

    check("HC-003 updated_true", updated_true, True)
    check("HC-003 remove called once", remove_mock.await_count, 1)
    check("HC-003 restart called once", mqtt_mock.await_count, 1)

    with (
        patch.object(javis_init.os.path, "exists", return_value=True),
        patch.object(
            javis_init,
            "load_json_file",
            return_value={"person": [{"person_id": "p001", "end_time": "2000-01-01"}]},
        ),
        patch.object(
            javis_init,
            "remove_expired_pids_from_face_sensor",
            AsyncMock(return_value=False),
        ),
        patch.object(
            javis_init, "restart_mqtt", AsyncMock(return_value=None)
        ) as mqtt_mock_false,
    ):
        updated_false = await javis_init.handle_person_data(hass)

    check("HC-003 updated_false", updated_false, False)
    check("HC-003 restart not called when unchanged", mqtt_mock_false.await_count, 0)


async def case_daily_scheduler_runs_independent_of_hrm_toggle():
    show_case(
        "HC-004",
        "Daily cleanup scheduler runs even when HRM sync is disabled",
        "setup_daily_expiry_cleanup with hrm_sync_enabled=false",
        "daily callback is registered and calls handle_person_data",
        "Daily cleanup must not depend on HRM sync toggle.",
    )

    hass = FakeHass()
    captured = {"callback": None}

    def fake_track_time_change(_hass, callback, hour, minute, second):
        captured["callback"] = callback
        captured["time"] = (hour, minute, second)
        return lambda: None

    with (
        patch.object(
            javis_init,
            "async_track_time_change",
            side_effect=fake_track_time_change,
        ),
        patch.object(
            javis_init, "handle_person_data", AsyncMock(return_value=False)
        ) as cleanup_mock,
    ):
        await javis_init.setup_daily_expiry_cleanup(hass)
        await captured["callback"](None)

    check_true("HC-004 callback captured", captured["callback"] is not None)
    check("HC-004 schedule at 00:05:00", captured["time"], (0, 5, 0))
    check("HC-004 cleanup called by callback", cleanup_mock.await_count, 1)


async def case_unload_cancels_daily_cleanup_listener():
    show_case(
        "HC-005",
        "Unloading entry cancels daily cleanup listener",
        "hass.data has daily_cleanup_listener + hrm_sync_listener",
        "both listeners are called and removed",
        "Prevents duplicated listeners after reload/unload cycles.",
    )

    hass = FakeHass()
    calls = {"hrm": 0, "daily": 0}

    def cancel_hrm():
        calls["hrm"] += 1

    def cancel_daily():
        calls["daily"] += 1

    hass.data[DOMAIN]["hrm_sync_listener"] = cancel_hrm
    hass.data[DOMAIN]["daily_cleanup_listener"] = cancel_daily
    hass.data[DOMAIN]["hrm_client"] = object()

    entry = SimpleNamespace(entry_id="entry-1")
    result = await javis_init.async_unload_entry(hass, entry)

    check("HC-005 unload returns True", result, True)
    check("HC-005 hrm listener cancelled", calls["hrm"], 1)
    check("HC-005 daily listener cancelled", calls["daily"], 1)
    check_true(
        "HC-005 hrm listener removed", "hrm_sync_listener" not in hass.data[DOMAIN]
    )
    check_true(
        "HC-005 daily listener removed",
        "daily_cleanup_listener" not in hass.data[DOMAIN],
    )
    check_true("HC-005 hrm client removed", "hrm_client" not in hass.data[DOMAIN])


async def main():
    await case_sync_calls_cleanup_without_places()
    await case_sync_calls_cleanup_when_queue_empty()
    await case_handle_person_data_reload_only_when_changed()
    await case_daily_scheduler_runs_independent_of_hrm_toggle()
    await case_unload_cancels_daily_cleanup_listener()


asyncio.run(main())

print("\n" + "=" * 60)
if tests_failed == 0:
    print(f"ALL {tests_run} TESTS PASSED")
else:
    print(f"FAILED: {tests_failed}/{tests_run}")
print("=" * 60 + "\n")

sys.exit(0 if tests_failed == 0 else 1)
