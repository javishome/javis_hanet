"""Script tests for service registration paths.

Run: python tests/test_services_registration.py
"""

import os
import sys
import voluptuous as vol

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import tests.conftest

import custom_components.javis_hanet.__init__ as javis_init
from custom_components.javis_hanet.const import (
    DOMAIN,
    SVC_CHECK_FACEID_GROUP_SENSOR,
    SVC_PUSH_TO_QCD,
    SVC_SET_HRM_SYNC_ENABLED,
    SVC_SET_HRM_SYNC_INTERVAL,
    SVC_SET_HRM_SYNC_LOG_ENABLED,
    SVC_SYNC_PERIODS,
    SVC_UPDATE_PERIOD,
    SVC_WRITE_PERSON,
)


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


class FakeServicesRegistry:
    def __init__(self):
        self.calls = []

    def register(self, *args, **kwargs):
        self.calls.append(("register", args, kwargs))

    def async_register(self, *args, **kwargs):
        self.calls.append(("async_register", args, kwargs))


class FakeHass:
    def __init__(self):
        self.services = FakeServicesRegistry()


def _services_from_calls(calls, method_name):
    return {args[1] for kind, args, _ in calls if kind == method_name}


def _schema_from_call(call):
    _, args, kwargs = call
    if "schema" in kwargs:
        return kwargs["schema"]
    if len(args) >= 4:
        return args[3]
    return None


print("\n" + "=" * 60)
print("TEST SERVICE REGISTRATION")
print("=" * 60)


show_case(
    "SR-001",
    "register_new publishes full service set",
    "Services.register_new()",
    "All 8 services are registered via hass.services.register",
    "New HA API path should expose interval + enable + log toggles.",
)
hass_new = FakeHass()
javis_init.Services(hass_new).register_new()

expected_new = {
    SVC_WRITE_PERSON,
    SVC_PUSH_TO_QCD,
    SVC_UPDATE_PERIOD,
    SVC_CHECK_FACEID_GROUP_SENSOR,
    SVC_SYNC_PERIODS,
    SVC_SET_HRM_SYNC_INTERVAL,
    SVC_SET_HRM_SYNC_ENABLED,
    SVC_SET_HRM_SYNC_LOG_ENABLED,
}
registered_new = _services_from_calls(hass_new.services.calls, "register")
check("register_new service set", registered_new, expected_new)
check("register_new call count", len(registered_new), 8)
check_true(
    "register_new domains are correct",
    all(
        args[0] == DOMAIN
        for kind, args, _ in hass_new.services.calls
        if kind == "register"
    ),
)


show_case(
    "SR-002",
    "register_old keeps legacy service set",
    "Services.register_old()",
    "6 services are registered via hass.services.async_register",
    "Legacy path does not include set_hrm_sync_enabled/log_enabled.",
)
hass_old = FakeHass()
javis_init.Services(hass_old).register_old()

expected_old = {
    SVC_WRITE_PERSON,
    SVC_PUSH_TO_QCD,
    SVC_UPDATE_PERIOD,
    SVC_CHECK_FACEID_GROUP_SENSOR,
    SVC_SYNC_PERIODS,
    SVC_SET_HRM_SYNC_INTERVAL,
}
registered_old = _services_from_calls(hass_old.services.calls, "async_register")
check("register_old service set", registered_old, expected_old)
check("register_old call count", len(registered_old), 6)
check_true(
    "register_old excludes hrm enable toggle",
    SVC_SET_HRM_SYNC_ENABLED not in registered_old,
)
check_true(
    "register_old excludes hrm log toggle",
    SVC_SET_HRM_SYNC_LOG_ENABLED not in registered_old,
)


show_case(
    "SR-003",
    "Schema validation for selected services",
    "write_person/set_hrm_sync_interval/set_hrm_sync_enabled schemas",
    "Required fields are enforced and coercion works",
    "Verifies input contract at service boundary.",
)
calls_by_name = {
    args[1]: call
    for call in hass_new.services.calls
    if call[0] == "register"
    for args in [call[1]]
}

write_schema = _schema_from_call(calls_by_name[SVC_WRITE_PERSON])
interval_schema = _schema_from_call(calls_by_name[SVC_SET_HRM_SYNC_INTERVAL])
enabled_schema = _schema_from_call(calls_by_name[SVC_SET_HRM_SYNC_ENABLED])

check_true("write_person schema exists", isinstance(write_schema, vol.Schema))
check_true(
    "set_hrm_sync_interval schema exists", isinstance(interval_schema, vol.Schema)
)
check_true("set_hrm_sync_enabled schema exists", isinstance(enabled_schema, vol.Schema))

check_true(
    "interval schema coerces string to int",
    interval_schema({"interval": "12"})["interval"] == 12,
)
check_true(
    "enabled schema accepts booleans",
    enabled_schema({"enabled": True})["enabled"] is True,
)

try:
    write_schema({})
    check_true("write_person requires payload", False)
except vol.Invalid:
    check_true("write_person requires payload", True)



# ------------------------------------------------------------
# Test service handler executions
# ------------------------------------------------------------
import asyncio
from types import SimpleNamespace

class FakeConfigEntries:
    def __init__(self):
        self.updated_entries = []

    def async_update_entry(self, entry, options):
        entry.options = options
        self.updated_entries.append((entry, options))


class FullFakeHass:
    def __init__(self):
        self.services = FakeServicesRegistry()
        self.config_entries = FakeConfigEntries()
        self.data = {}

    def async_create_task(self, coro):
        pass


async def run_async_service_tests():
    fake_entry = SimpleNamespace(options={"hrm_sync_interval": 30, "hrm_sync_enabled": True, "hrm_sync_log_enabled": False})
    hass = FullFakeHass()
    hass.data[DOMAIN] = {"entry": fake_entry}

    # Mock setup_hrm_sync to avoid real network/timers in test
    original_setup = javis_init.setup_hrm_sync
    async def mock_setup(h, e):
        pass
    javis_init.setup_hrm_sync = mock_setup

    try:
        svc = javis_init.Services(hass)

        show_case(
            "SR-004",
            "set_hrm_sync_interval rejects interval < 5",
            "call with interval=3",
            "status=error",
            "Safety limit against high-frequency API polling",
        )
        res_reject = await svc.set_hrm_sync_interval(SimpleNamespace(data={"interval": 3}))
        check("interval < 5 error status", res_reject.get("status"), "error")

        show_case(
            "SR-005",
            "set_hrm_sync_interval updates entry options when interval >= 5",
            "call with interval=60",
            "status=ok and entry.options[hrm_sync_interval] == 60",
            "Applies dynamic interval reconfiguration",
        )
        res_ok = await svc.set_hrm_sync_interval(SimpleNamespace(data={"interval": 60}))
        check("interval >= 5 success status", res_ok.get("status"), "ok")
        check("entry option interval updated", fake_entry.options.get("hrm_sync_interval"), 60)

        show_case(
            "SR-006",
            "set_hrm_sync_enabled and set_hrm_sync_log_enabled toggle options",
            "toggling sync enabled to False and log enabled to True",
            "status=ok and entry options updated",
            "Dynamic toggles for syncing and logging",
        )
        res_sync_toggle = await svc.set_hrm_sync_enabled(SimpleNamespace(data={"enabled": False}))
        check("sync toggle status", res_sync_toggle.get("status"), "ok")
        check("sync option updated", fake_entry.options.get("hrm_sync_enabled"), False)

        res_log_toggle = await svc.set_hrm_sync_log_enabled(SimpleNamespace(data={"enabled": True}))
        check("log toggle status", res_log_toggle.get("status"), "ok")
        check("log option updated", fake_entry.options.get("hrm_sync_log_enabled"), True)

        show_case(
            "SR-007",
            "check_faceid_group_sensor invokes handle_person_data",
            "call check_faceid_group_sensor",
            "status=ok",
            "Manual sensor reconciliation service",
        )
        original_handle_person = javis_init.handle_person_data
        async def mock_handle_person(h):
            pass
        javis_init.handle_person_data = mock_handle_person
        try:
            res_sensor = await svc.check_faceid_group_sensor(SimpleNamespace(data={}))
            check("check_faceid_group_sensor status", res_sensor.get("status"), "ok")
        finally:
            javis_init.handle_person_data = original_handle_person
    finally:
        javis_init.setup_hrm_sync = original_setup


        show_case(
            "SR-008",
            "sync_periods handler returns ok when sync_periods_api is True",
            "call sync_periods",
            "status=ok",
            "Service response status handling",
        )
        original_sync = javis_init.sync_periods_api
        async def mock_sync_ok(h):
            return True
        javis_init.sync_periods_api = mock_sync_ok
        try:
            res_sync_ok = await svc.sync_periods(SimpleNamespace(data={}))
            check("sync_periods ok status", res_sync_ok.get("status"), "ok")
        finally:
            javis_init.sync_periods_api = original_sync

        show_case(
            "SR-009",
            "sync_periods handler returns error when sync_periods_api is False or raises",
            "call sync_periods with failure",
            "status=error",
            "Service error response",
        )
        async def mock_sync_fail(h):
            return False
        javis_init.sync_periods_api = mock_sync_fail
        try:
            res_sync_fail = await svc.sync_periods(SimpleNamespace(data={}))
            check("sync_periods fail status", res_sync_fail.get("status"), "error")
        finally:
            javis_init.sync_periods_api = original_sync

asyncio.run(run_async_service_tests())

print("\n" + "=" * 60)
if tests_failed == 0:
    print(f"ALL {tests_run} TESTS PASSED")
else:
    print(f"FAILED: {tests_failed}/{tests_run}")
print("=" * 60 + "\n")

sys.exit(0 if tests_failed == 0 else 1)
