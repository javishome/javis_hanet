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


print("\n" + "=" * 60)
if tests_failed == 0:
    print(f"ALL {tests_run} TESTS PASSED")
else:
    print(f"FAILED: {tests_failed}/{tests_run}")
print("=" * 60 + "\n")

sys.exit(0 if tests_failed == 0 else 1)
