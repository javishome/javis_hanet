"""Script tests for manifest version bump behavior.

Run: python tests/test_versioning.py
"""

import json
import os
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import auto_encode as release_tool


tests_run = 0
tests_failed = 0

today_version = datetime.now().strftime("v%Y%m%d")


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


def expect_raises_value_error(test_name, func, value):
    global tests_run, tests_failed
    tests_run += 1
    try:
        func(value)
        tests_failed += 1
        print(f"  FAIL: {test_name}")
        print("        Expected ValueError but no exception was raised")
    except ValueError:
        print(f"  PASS: {test_name}")


print("\n" + "=" * 60)
print("TEST VERSION LOGIC (auto_encode.py)")
print("=" * 60)


show_case(
    "V-001",
    "Return date-based version",
    "any_string",
    today_version,
    "Should ignore input and return today's datestring",
)
check("_bump_version_tag('v1')", release_tool._bump_version_tag("v1"), today_version)
check("_bump_version_tag('1')", release_tool._bump_version_tag("1"), today_version)
check("_bump_version_tag('invalid')", release_tool._bump_version_tag("invalid"), today_version)

show_case(
    "V-005",
    "Update manifest file from v-format",
    '{"version": "v1"}',
    f'old="v1", new="{today_version}", file version="{today_version}"',
    "Avoid unicode print issues by mocking print in this test.",
)
with tempfile.TemporaryDirectory() as tmp:
    manifest_path = os.path.join(tmp, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"version": "v1"}, f)

    with patch("builtins.print"):
        old_version, new_version = release_tool.update_manifest_version(tmp)

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    check("update_manifest_version old", old_version, "v1")
    check("update_manifest_version new", new_version, today_version)
    check(f"manifest file updated to {today_version}", data["version"], today_version)


show_case(
    "V-006",
    "Update manifest file from legacy numeric format",
    '{"version": "1"}',
    f'old="1", new="{today_version}", file version="{today_version}"',
    "Ensures migration path for existing repos.",
)
with tempfile.TemporaryDirectory() as tmp:
    manifest_path = os.path.join(tmp, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"version": "1"}, f)

    with patch("builtins.print"):
        old_version, new_version = release_tool.update_manifest_version(tmp)

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    check("legacy old version", old_version, "1")
    check("legacy new version", new_version, today_version)
    check("legacy manifest rewritten", data["version"], today_version)


show_case(
    "V-007",
    "Invalid manifest version should be fully overwritten by date-based",
    '{"version": "alpha"}',
    f'old="alpha", new="{today_version}", file version="{today_version}"',
    "Safe migration from any string.",
)
with tempfile.TemporaryDirectory() as tmp:
    manifest_path = os.path.join(tmp, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"version": "alpha"}, f)

    with patch("builtins.print"):
        old_version, new_version = release_tool.update_manifest_version(tmp)

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    check("invalid format old version", old_version, "alpha")
    check("invalid format new version", new_version, today_version)
    check_true("file version updated", data["version"] == today_version)


show_case(
    "V-008",
    "Interactive prompt accepts keep-version=yes",
    "stdin is TTY, user input='y'",
    "returns True",
    "Main flow should keep version when user confirms.",
)
with (
    patch.object(
        release_tool, "sys", SimpleNamespace(stdin=SimpleNamespace(isatty=lambda: True))
    ),
    patch("builtins.input", return_value="y"),
):
    keep_true = release_tool.should_keep_current_version()
check("should_keep_current_version('y')", keep_true, True)


show_case(
    "V-009",
    "Interactive prompt default path",
    "stdin is TTY, user presses Enter",
    "returns False",
    "Enter should map to default No (auto bump).",
)
with (
    patch.object(
        release_tool, "sys", SimpleNamespace(stdin=SimpleNamespace(isatty=lambda: True))
    ),
    patch("builtins.input", return_value=""),
):
    keep_false = release_tool.should_keep_current_version()
check("should_keep_current_version('')", keep_false, False)


show_case(
    "V-010",
    "Non-interactive mode fallback",
    "stdin is not TTY",
    "returns False",
    "CI/non-interactive runs should auto-bump without waiting for input.",
)
with (
    patch.object(
        release_tool,
        "sys",
        SimpleNamespace(stdin=SimpleNamespace(isatty=lambda: False)),
    ),
    patch("builtins.print"),
):
    keep_non_tty = release_tool.should_keep_current_version()
check("should_keep_current_version(non-tty)", keep_non_tty, False)


print("\n" + "=" * 60)
if tests_failed == 0:
    print(f"ALL {tests_run} TESTS PASSED")
else:
    print(f"FAILED: {tests_failed}/{tests_run}")
print("=" * 60 + "\n")

sys.exit(0 if tests_failed == 0 else 1)
