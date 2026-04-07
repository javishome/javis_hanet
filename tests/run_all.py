"""
Chạy toàn bộ Test Suite cho Javis Hanet Component.
Lệnh: python tests/run_all.py
"""

import subprocess
import sys
import os

os.chdir(os.path.join(os.path.dirname(__file__), ".."))

TEST_FILES = [
    "tests/test_run.py",
    "tests/test_proof.py",
    "tests/test_utils.py",
    "tests/test_architecture.py",
    "tests/test_sync_logic.py",
    "tests/test_hrm_api.py",
    "tests/test_versioning.py",
    "tests/test_services_registration.py",
    "tests/test_service_update_period.py",
    "tests/test_sync_periods_api.py",
    "tests/test_hrm_auto_cleanup.py",
]

total_pass = 0
total_fail = 0
results = []

print("\n" + "═" * 60)
print("🚀 JAVIS HANET - CHẠY TOÀN BỘ TEST SUITE")
print("═" * 60)

for test_file in TEST_FILES:
    basename = os.path.basename(test_file)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, test_file],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    if result.returncode == 0:
        total_pass += 1
        results.append((basename, "✅ PASS"))
    else:
        total_fail += 1
        results.append((basename, "❌ FAIL"))

    # In output của từng file
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    if stdout.strip():
        print(stdout)
    if result.returncode != 0 and stderr.strip():
        print(stderr)

# ── Bảng tổng kết ──
print("═" * 60)
print("📊 BẢNG TỔNG KẾT")
print("═" * 60)
for name, status in results:
    print(f"  {status}  {name}")

print("─" * 60)
if total_fail == 0:
    print(f"  🎉 {total_pass}/{total_pass} FILES PASSED - HỆ THỐNG AN TOÀN!")
else:
    print(f"  💥 {total_fail}/{total_pass + total_fail} FILES FAILED!")
print("═" * 60 + "\n")

sys.exit(0 if total_fail == 0 else 1)
