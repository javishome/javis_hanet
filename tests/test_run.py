"""Quick smoke test: Chỉ kiểm tra xem main_code/2024 có import được không.

Chạy bằng lệnh: python tests/test_run.py
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import tests.conftest

# ── IMPORT THẲNG TỪ CODE GỐC ────────────────────────────────────────
try:
    from custom_components.javis_hanet.__init__ import async_unload_entry, restart_mqtt, DOMAIN, PERSON_FILE_LOCK
    from custom_components.javis_hanet.config_flow import HanetOptionsFlow
    from custom_components.javis_hanet.hrm_api import HRMClient
    from custom_components.javis_hanet.utils import yaml2dict, dict2yaml, get_host
    from custom_components.javis_hanet.const import HOST1, HOST2, HOST3

    print("✅ SUCCESS - Tất cả module đều import thành công!")
    print(f"   DOMAIN = {DOMAIN}")
    print(f"   PERSON_FILE_LOCK = {PERSON_FILE_LOCK}")
    print(f"   HRMClient = {HRMClient}")
    print(f"   HanetOptionsFlow = {HanetOptionsFlow}")
    print(f"   Hosts = {HOST1}, {HOST2}, {HOST3}")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"\n❌ FAIL: {e}")
    sys.exit(1)
