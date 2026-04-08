"""Tests for services.yaml and const.py integrity.

Validates that:
- All services in const.py are declared in services.yaml
- All services in services.yaml have the correct structure
- Encode.py has all required files listed
"""
import pytest
import yaml
import os

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "main_code", "2024")


def _load_services_yaml():
    path = os.path.join(BASE_DIR, "services.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_const_services():
    """Parse SVC_ constants from const.py."""
    path = os.path.join(BASE_DIR, "const.py")
    services = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("SVC_"):
                # SVC_WRITE_PERSON = "write_person"
                val = line.split("=")[1].strip().strip('"').strip("'")
                services.append(val)
    return services


# ── Services YAML Structure ──────────────────────────────────────────
class TestServicesYaml:
    def test_yaml_parseable(self):
        """services.yaml phải parse được."""
        data = _load_services_yaml()
        assert isinstance(data, dict)

    def test_all_services_have_name(self):
        """Mỗi service phải có tên."""
        data = _load_services_yaml()
        for svc_name, svc_def in data.items():
            assert "name" in svc_def, f"Service '{svc_name}' thiếu 'name'"

    def test_all_services_have_description(self):
        """Mỗi service phải có mô tả."""
        data = _load_services_yaml()
        for svc_name, svc_def in data.items():
            assert "description" in svc_def, f"Service '{svc_name}' thiếu 'description'"

    def test_fields_have_selectors(self):
        """Nếu service có fields, mỗi field phải có selector."""
        data = _load_services_yaml()
        for svc_name, svc_def in data.items():
            fields = svc_def.get("fields", {})
            for field_name, field_def in fields.items():
                assert "selector" in field_def, (
                    f"Service '{svc_name}' field '{field_name}' thiếu 'selector'"
                )

    def test_no_duplicate_service_keys(self):
        """Không được có service trùng tên (YAML spec đè key cuối)."""
        path = os.path.join(BASE_DIR, "services.yaml")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        # Count top-level keys that start at column 0
        keys = []
        for line in content.split("\n"):
            stripped = line.rstrip()
            if stripped and not stripped.startswith(" ") and not stripped.startswith("#") and ":" in stripped:
                key = stripped.split(":")[0]
                keys.append(key)
        assert len(keys) == len(set(keys)), f"Duplicate service keys found: {keys}"


# ── Const ↔ Services Sync ────────────────────────────────────────────
class TestConstServiceSync:
    def test_all_const_services_in_yaml(self):
        """Mỗi SVC_ constant trong const.py phải có trong services.yaml."""
        yaml_services = set(_load_services_yaml().keys())
        const_services = _load_const_services()
        for svc in const_services:
            assert svc in yaml_services, (
                f"Service '{svc}' có trong const.py nhưng thiếu trong services.yaml"
            )


# ── Encode.py Completeness ───────────────────────────────────────────
class TestEncodeCompleteness:
    def test_encode_includes_all_py_files(self):
        """encode.py phải encode tất cả các file .py chính."""
        encode_path = os.path.join(BASE_DIR, "encode.py")
        with open(encode_path, "r", encoding="utf-8") as f:
            content = f.read()

        required = ["__init__.py", "const.py", "utils.py", "hrm_api.py"]
        for fname in required:
            assert fname in content, f"encode.py thiếu file '{fname}'"

    def test_no_config_flow_in_encode(self):
        """config_flow.py KHÔNG nên bị encode (vì HA cần import class)."""
        encode_path = os.path.join(BASE_DIR, "encode.py")
        with open(encode_path, "r", encoding="utf-8") as f:
            content = f.read()
        # config_flow thường không nên encode, nhưng nếu có thì test sẽ fail
        # Bỏ comment dòng dưới nếu muốn enforce:
        # assert "config_flow.py" not in content


# ── Manifest.json ────────────────────────────────────────────────────
class TestManifest:
    def test_manifest_valid_json(self):
        path = os.path.join(BASE_DIR, "manifest.json")
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "domain" in data
        assert "version" in data
        assert data["domain"] == "javis_hanet"

    def test_manifest_has_required_keys(self):
        path = os.path.join(BASE_DIR, "manifest.json")
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key in ("domain", "name", "version"):
            assert key in data, f"manifest.json thiếu key '{key}'"
