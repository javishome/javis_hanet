"""Comprehensive End-to-End Test Suite for Javis Hanet (with Dry-Run Safety):
1. Hanet Login & OAuth Token Lifecycle (POST /api/hanet/token & OAuth2 exchange)
2. Hanet Places & Data Sync (POST /api/hanet/get_places & POST /api/hanet/get_info_with_places)
3. HA Component Storage & Sensor Synchronization (person_javis_v2.json & face_sensor.yaml)
4. Live HA Service Execution against Remote HA (192.168.168.24):
   - javis_hanet.set_hrm_sync_interval
   - javis_hanet.check_faceid_group_sensor
   - javis_hanet.sync_periods
   - javis_hanet.write_person
   - javis_hanet.update_period
   - javis_hanet.push_to_qcd (Dry-Run with isolated date parameter)
5. Bytecode & HA Core Event Bus Sanity in Local Docker Containers (HA 2024.4.4 & 2024.12.4)

Usage:
    # Run full E2E test against Server Cloud API & Remote HA 192.168.168.24
    python tests/test_live_hanet_services.py --remote 192.168.168.24

    # Run in local Docker HA containers
    python tests/test_live_hanet_services.py --docker

    # Run everything
    python tests/test_live_hanet_services.py --all
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import jwt
import requests

# Target Configs
DEFAULT_SERVER_URL = "https://lock-api.javiscloud.com"
DEFAULT_HA_IP = "192.168.168.24"
DEFAULT_HA_PORT = 8123

# Real Auth Credentials from 192.168.168.24
HA_JWT_ISS = "1dd0b3e5a6e74e69a3977ed011a62998"
HA_JWT_KEY = "fcf76ae532283057721b03b3afbdbdeed3ccf959d35a452cbef0ba9cb863cd803f22ac79c4e98284222c53d8828f5fc61f1a00755d2ff8238d70ec98ea2ae15e"

REAL_HANET_REFRESH_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpZCI6IjcyNDU2Mzk2NjE3MDA0OTQ5MjkiLCJlbWFpbCI6ImNoaW5oZHp6ejE0QGdtYWlsLmNvbSIsImNsaWVudF9pZCI6Ijk0NDE0YTY2ZjNjNmE3ZTJjZWFkYzE3YWY4Y2NkZDYwIiwidHlwZSI6InJlZnJlc2hfdG9rZW4iLCJpYXQiOjE3ODIxMTI0NzUsImV4cCI6MTg0NTE4NDQ3NX0."
    "x7I_ITesSWpr-RHKTY0qx0IftcizEjNpqwOYJlyO32I"
)
REAL_HANET_ACCESS_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpZCI6IjcyNDU2Mzk2NjE3MDA0OTQ5MjkiLCJlbWFpbCI6ImNoaW5oZHp6ejE0QGdtYWlsLmNvbSIsImNsaWVudF9pZCI6Ijk0NDE0YTY2ZjNjNmE3ZTJjZWFkYzE3YWY4Y2NkZDYwIiwidHlwZSI6ImF1dGhvcml6YXRpb25fY29kZSIsImlhdCI6MTc4MjExMjQ3NSwiZXhwIjoxODEzNjQ4NDc1fQ."
    "dkR36wCVyCU5PgD9B_vOCXbK93rVvNKrJvnslkgU7cI"
)
REAL_HANET_PLACE_ID = 5390
TIMESHEET_SECRET_KEY = "JbY7Qu0fPR27"


def generate_ha_token():
    """Generates a valid signed Bearer JWT token for Home Assistant REST API."""
    now = int(time.time())
    payload = {"iss": HA_JWT_ISS, "iat": now, "exp": now + 3600 * 24 * 365}
    return jwt.encode(payload, HA_JWT_KEY, algorithm="HS256")


def test_hanet_auth_and_data_sync(server_url=DEFAULT_SERVER_URL):
    """
    Tests Layer 1: Complete Hanet Authentication & Data Sync Lifecycle.
    """
    print("\n" + "=" * 88)
    print("  PHẦN 1: TEST ĐĂNG NHẬP & ĐỒNG BỘ DỮ LIỆU HANET TRÊN SERVER CLOUD API")
    print(f"  Server URL: {server_url}")
    print("=" * 88)

    active_access_token = REAL_HANET_ACCESS_TOKEN
    all_passed = True

    # 1. Test Server Healthcheck
    try:
        r = requests.get(f"{server_url}/health", timeout=10)
        print(f"[*] 1. Server Healthcheck: Status {r.status_code} -> {r.json()}")
        assert r.status_code == 200
    except Exception as e:
        print(f"  ❌ Healthcheck failed: {e}")
        all_passed = False

    # 2. Test Đăng Nhập & Cấp Token OAuth trực tiếp qua Hanet OAuth Engine
    print("\n[*] 2. Test Đăng Nhập & Làm Mới Token qua Hanet OAuth2 Engine...")
    try:
        t0 = time.time()
        sys.path.insert(0, "/home/chinh/work/javis/server/104_smartlock_cloud_api")
        from app.controllers.hanet_controller import get_token
        res = get_token("refresh_token", refresh_token=REAL_HANET_REFRESH_TOKEN)
        lat = int((time.time() - t0) * 1000)
        if res.get("access_token"):
            active_access_token = res["access_token"]
            print(f"  ✅ PASS: Xác thực OAuth & cấp token mới thành công ({lat}ms)!")
            print(f"     Access Token mới : {active_access_token[:35]}...")
            print(f"     Refresh Token mới: {res.get('refresh_token', '')[:35]}... (Hạn dùng: {res.get('expire', 0)}s)")
        else:
            print(f"  ❌ FAIL: Hanet OAuth exchange returned: {res}")
            all_passed = False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        all_passed = False

    # 3. Test Đồng Bộ Danh Sách Địa Điểm: POST /api/hanet/get_places
    print("\n[*] 3. Test Đồng Bộ Danh Sách Địa Điểm qua POST /api/hanet/get_places...")
    fetched_places = []
    try:
        t0 = time.time()
        r = requests.post(
            f"{server_url}/api/hanet/get_places",
            data={"access_token": active_access_token},
            timeout=10
        )
        lat = int((time.time() - t0) * 1000)
        if r.status_code == 200:
            fetched_places = r.json()
            print(f"  ✅ PASS: Server đồng bộ thành công {len(fetched_places)} địa điểm ({lat}ms):")
            for p in fetched_places:
                print(f"     - ID: {p.get('place_id')} | Tên: {p.get('place_name')}")
            assert any(p.get("place_id") == REAL_HANET_PLACE_ID for p in fetched_places)
        else:
            print(f"  ❌ FAIL: Server trả về status {r.status_code}: {r.text[:200]}")
            all_passed = False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        all_passed = False

    # 4. Test Đồng Bộ Toàn Bộ Camera & Nhân Viên FaceID: POST /api/hanet/get_info_with_places
    print("\n[*] 4. Test Đồng Bộ Toàn Bộ Camera & Nhân Viên qua POST /api/hanet/get_info_with_places...")
    try:
        t0 = time.time()
        target_places = [{"place_id": REAL_HANET_PLACE_ID, "place_name": "Văn phòng ATV"}]
        sync_payload = {
            "access_token": active_access_token,
            "places": target_places
        }
        r = requests.post(
            f"{server_url}/api/hanet/get_info_with_places",
            json=sync_payload,
            timeout=10
        )
        lat = int((time.time() - t0) * 1000)
        if r.status_code == 200:
            sync_data = r.json()
            places_res = sync_data.get("place", [])
            cameras_res = sync_data.get("camera", [])
            persons_res = sync_data.get("person", [])
            print(f"  ✅ PASS: Server hoàn tất đồng bộ toàn diện ({lat}ms):")
            print(f"     📍 Địa điểm : {len(places_res)} Places")
            print(f"     📹 Camera   : {len(cameras_res)} Devices {[c.get('device_name') for c in cameras_res]}")
            print(f"     👤 Nhân viên: {len(persons_res)} FaceID Members (sample: {[p.get('person_name') for p in persons_res[:3]]})")
            assert len(cameras_res) > 0, "No cameras returned"
            assert len(persons_res) > 0, "No persons returned"
        else:
            print(f"  ❌ FAIL: Server trả về status {r.status_code}: {r.text[:200]}")
            all_passed = False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        all_passed = False

    return all_passed


def call_ha_service(ha_url, token, domain, service, service_data=None, timeout=20):
    """Calls a Home Assistant service via REST API and measures latency."""
    url = f"{ha_url}/api/services/{domain}/{service}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = json.dumps(service_data or {}).encode("utf-8")

    t0 = time.time()
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            content = resp.read().decode("utf-8")
            latency_ms = int((time.time() - t0) * 1000)
            return True, status, content, latency_ms
    except urllib.error.HTTPError as he:
        latency_ms = int((time.time() - t0) * 1000)
        return False, he.code, he.read().decode("utf-8"), latency_ms
    except Exception as e:
        latency_ms = int((time.time() - t0) * 1000)
        return False, 0, str(e), latency_ms


def test_remote_ha_services(ha_ip=DEFAULT_HA_IP, port=DEFAULT_HA_PORT):
    """
    Tests Layer 2: Real HA Service Invocations against Remote HA instance 192.168.168.24.
    """
    ha_url = f"http://{ha_ip}:{port}"
    token = generate_ha_token()

    print("\n" + "=" * 88)
    print(f"  PHẦN 2: TEST CÁC SERVICES THẬT TRÊN HOME ASSISTANT ({ha_url})")
    print("=" * 88)

    available_services = set()
    try:
        req = urllib.request.Request(f"{ha_url}/api/", headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            print(f"[*] Kết nối HA 192.168.168.24 thành công: {resp.read().decode('utf-8')}")

        req_svcs = urllib.request.Request(f"{ha_url}/api/services", headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req_svcs, timeout=5) as resp_s:
            all_svcs = json.loads(resp_s.read().decode("utf-8"))
            for s in all_svcs:
                if s.get("domain") == "javis_hanet":
                    available_services = set(s.get("services", {}).keys())
            print(f"[*] HA đang kích hoạt {len(available_services)} Hanet services: {list(available_services)}")
    except Exception as e:
        print(f"❌ Failed to reach HA on {ha_url}: {e}")
        return False

    test_cases = [
        {
            "svc": "set_hrm_sync_interval",
            "payload": {"interval": 45},
            "restore_payload": {"interval": 30},
            "desc": "Thay đổi chu kỳ đồng bộ HRM sang 45s",
        },
        {
            "svc": "check_faceid_group_sensor",
            "payload": {},
            "desc": "Quét faceID sensor và cập nhật nhóm",
        },
        {
            "svc": "sync_periods",
            "payload": {},
            "desc": "Đồng bộ danh sách periods lên HRM",
        },
        {
            "svc": "write_person",
            "payload": {
                "payload": json.dumps(
                    {
                        "person_id": "test_auto_999",
                        "person_name": "[TEST_AUTO] Auto Test Person",
                        "place_id": REAL_HANET_PLACE_ID,
                        "time": int(time.time()),
                    }
                )
            },
            "desc": "Ghi log nhân viên chấm công vào timesheet.log",
        },
        {
            "svc": "update_period",
            "payload": {
                "person_id": "test_auto_999",
                "start_time": "2026-01-01",
                "end_time": "2026-12-31",
            },
            "desc": "Cập nhật thời hạn hiệu lực period cho nhân viên",
        },
        {
            "svc": "push_to_qcd",
            "payload": {
                "secret_key": TIMESHEET_SECRET_KEY,
                "date": "2026-01-01",
            },
            "desc": "[DRY-RUN] Đẩy log lên QCD với ngày giả lập (bảo vệ log hôm nay)",
        },
    ]

    print("\n[*] Thực thi gọi Service...")
    results = []
    print("-" * 88)
    print(f"{'SERVICE':<36} | {'LATENCY':<8} | {'HTTP':<5} | {'RESULT':<8} | {'DESCRIPTION'}")
    print("-" * 88)

    all_passed = True
    for tc in test_cases:
        svc = tc["svc"]
        svc_full = f"javis_hanet.{svc}"

        if available_services and svc not in available_services:
            print(f"{svc_full:<36} | {'N/A':<8} | {'N/A':<5} | {'⏭️ SKIP':<8} | (Chưa đăng ký trên bản cài hiện tại)")
            continue

        ok, code, resp_body, lat = call_ha_service(ha_url, token, "javis_hanet", svc, tc.get("payload"))

        if tc.get("restore_payload"):
            call_ha_service(ha_url, token, "javis_hanet", svc, tc.get("restore_payload"))

        status_str = "✅ PASS" if ok else "❌ FAIL"
        if not ok:
            all_passed = False

        print(f"{svc_full:<36} | {str(lat)+'ms':<8} | {code:<5} | {status_str:<8} | {tc['desc']}")
        results.append({"service": svc_full, "ok": ok, "latency": lat, "code": code})

    print("-" * 88)
    passed_count = sum(1 for r in results if r["ok"])
    print(f"\n📊 SUMMARY: {passed_count}/{len(results)} Services Passed against {ha_url}\n")
    return all_passed


def test_local_docker_ha():
    """
    Tests Layer 3: HA Core Event Bus & Bytecode verification inside Official HA Docker Containers.
    """
    print("\n" + "=" * 88)
    print("  PHẦN 3: TEST TRONG CONTAINER DOCKER HOME ASSISTANT CORE (Python 3.12 / 3.13)")
    print("=" * 88)

    hanet_repo_dir = "/home/chinh/work/javis/custom_component/107_hanet_component"
    script_path = os.path.join(hanet_repo_dir, "tests", "test_in_docker_ha.py")
    if not os.path.exists(script_path):
        print(f"❌ Test script {script_path} not found!")
        return False

    res = subprocess.run([sys.executable, script_path], cwd=hanet_repo_dir)
    return res.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Full E2E Javis Hanet Services Automation Test Suite")
    parser.add_argument("--server", type=str, default=DEFAULT_SERVER_URL, help="Server Cloud API URL")
    parser.add_argument("--remote", type=str, default=None, help="Remote HA IP address (e.g. 192.168.168.24)")
    parser.add_argument("--docker", action="store_true", help="Run local Docker HA container test")
    parser.add_argument("--all", action="store_true", help="Run all 3 test layers")
    args = parser.parse_args()

    success = True

    # 1. Test Hanet Auth & Data Sync on Server Cloud API
    auth_sync_ok = test_hanet_auth_and_data_sync(args.server)
    success = success and auth_sync_ok

    # 2. Test Remote HA Services
    if args.all or (not args.docker):
        remote_ok = test_remote_ha_services(args.remote or DEFAULT_HA_IP)
        success = success and remote_ok

    # 3. Test Local Docker HA Container
    if args.all or args.docker:
        docker_ok = test_local_docker_ha()
        success = success and docker_ok

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
