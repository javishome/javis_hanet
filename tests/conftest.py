import os
import sys
import types
import importlib.util
from importlib.machinery import ModuleSpec

# ── HA MOCK IMPORTER (Định tuyến 2024 -> custom_components.javis_hanet) ──
# Tính toán đường dẫn gốc tới main_code/2024
pkg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../main_code/2024"))

class CustomComponentImporter:
    """Mock importer để biến thư mục main_code/2024 thành package `custom_components.javis_hanet` hợp lệ trong Python 3+"""
    
    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        if fullname.startswith("custom_components.javis_hanet"):
            rel_path = fullname.replace("custom_components.javis_hanet", "").replace(".", os.sep)
            
            if rel_path == "":
                filepath = os.path.join(pkg_path, "__init__.py")
                is_pkg = True
            else:
                filepath = os.path.join(pkg_path, rel_path.lstrip(os.sep) + ".py")
                is_pkg = False
                
            if not os.path.exists(filepath):
                return None
                
            spec = importlib.util.spec_from_file_location(fullname, filepath)
            if is_pkg:
                spec.submodule_search_locations = [pkg_path]
            return spec
            
        return None

# Tạo nhánh cha custom_components vào sys.modules trước
if "custom_components" not in sys.modules:
    sys.modules["custom_components"] = types.ModuleType("custom_components")
    sys.modules["custom_components"].__path__ = []

# Đảm bảo subpackage có thể resolve package cha
if "custom_components.javis_hanet" not in sys.modules:
    sys.meta_path.insert(0, CustomComponentImporter)

# ── PYTEST CONFIG FIXTURES (Dành riêng cho Home Assistant) ──
import pytest
import asyncio

# Sửa lỗi chí mạng trên Windows: ProactorEventLoop mặc định của Windows gọi hàm socket.socket()
# để mở pipe giao tiếp nội bộ. Tuy nhiên thư viện `pytest-homeassistant-custom-component`
# lại chặn đứng ngặt nghèo socket.socket(). Kết quả là văng lỗi SocketBlockedError ngay Vòng Gửi Xe.
# Cách giải quyết chuẩn mực cho Windows: Chuyển sang dùng SelectorEventLoopPolicy.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Chỉ kích hoạt nếu pytest-homeassistant-custom-component đã được cài đặt
try:
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    
    @pytest.fixture
    def mock_config_entry():
        """Tạo một ConfigEntry giả để test."""
        return MockConfigEntry(
            domain="javis_hanet",
            data={
                "account_type": "hanet",
                "token": {"access_token": "fake", "userID": "user1", "email": "a@b.com"},
                "selected_places": [{"place_id": 5390, "place_name": "VP"}],
            },
            options={
                "hrm_sync_enabled": False,
                "hrm_sync_log_enabled": False,
                "hrm_sync_interval": 30,
            },
        )
except ImportError:
    pass
