import asyncio
from .const import *
import json
import os
from homeassistant.const import __version__ as ha_version
import logging
import aiohttp
from datetime import datetime
import yaml
import traceback

LOGGER = logging.getLogger(__name__)

def write_data(data):
    with open(PATH, "w", encoding="utf-8") as json_file:
        json.dump(
            data, json_file, ensure_ascii=False, indent=4
        )  # indent=4 for pretty formatting


def remove_data():
    if os.path.exists(PATH):
        os.remove(PATH)

def is_new_version():
    year, version = ha_version.split(".")[:2]
    if int(year) >= 2024 and int(version) >= 7:
        return True
    return False

def write_data_log_qcd(data):
    # check if folder exist
    if not os.path.exists(FOLDER_PERSON_LOG):
        os.makedirs(FOLDER_PERSON_LOG)
    # convert data to string and add to file
    with open(PATH_PERSON_LOG, "a", encoding="utf-8") as txt_file:
        txt_file.write(str(data) + "\n")


def _rotate_and_read_log(date_str=None):
    if not date_str:
        if not os.path.exists(PATH_PERSON_LOG):
            return "NO_FILE", None
        new_file_name = datetime.now().strftime("%y%m%d") + ".log"
    else:
        try:
            new_file_name = datetime.strptime(date_str, "%Y-%m-%d").strftime("%y%m%d") + ".log"
        except ValueError:
            LOGGER.error("Invalid date format. Use YYYY-MM-DD.")
            return "INVALID_DATE", None
    new_file_path = FOLDER_PERSON_LOG + new_file_name
    try:
        os.rename(PATH_PERSON_LOG, new_file_path)
    except Exception as e:
        LOGGER.error(f"Error renaming {PATH_PERSON_LOG} to {new_file_path}: {e}")
        return False, None

    if not os.path.exists(new_file_path):
        LOGGER.error(f"File {new_file_path} does not exist.")
        return False, None

    payload = []
    with open(new_file_path, encoding="utf-8") as txt_file:
        file_content = txt_file.read()
        for line in file_content.split("\n"):
            if not line:
                continue
            line = line.replace("'", '"')
            data = json.loads(line)
            payload.append(data)
    return new_file_path, payload


async def change_file_name(secret_key, date_str=None):
    new_file_path, payload = await asyncio.to_thread(_rotate_and_read_log, date_str)
    if new_file_path == "INVALID_DATE" or new_file_path == "NO_FILE":
        return None
    if not new_file_path:
        return False

    qcd_url = "https://qcd.arrow-tech.vn/api/v2/resum-timesheet"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "timesheet_secret_key": secret_key,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(qcd_url, json=payload, headers=headers) as response:
            info = await response.json()
            if response.status != 200:
                LOGGER.error(info)
                return False
            else:
                LOGGER.info(f"Successfully sent data to QCD: {info}")
                return True


def get_host(add_url):

    """Get the url from the config entry."""
    if MODE == "dev" or MODE == "dev_ha_real":
        return SERVER_URL
    return SERVER_URL + add_url


def get_hc_url(add_url):
    """Get the url from the config entry."""
    if MODE == "dev":
        return "http://127.0.0.1:8123"
    else:
        mac, source, mac_address = _get_mac_details()
        base_url = f"https://{mac}.{add_url}"
        LOGGER.info(
            "Generated Home Controller URL: url=%s mac_decimal=%s mac=%s source=%s",
            base_url,
            mac,
            mac_address,
            source,
        )
    return base_url


def _mac_to_decimal(mac_address):
    normalized = mac_address.strip().lower().replace(":", "").replace("-", "")
    if len(normalized) != 12:
        raise ValueError(f"Invalid MAC address length: {mac_address}")
    int(normalized, 16)
    return int(normalized, 16)


def _read_interface_mac(interface):
    if not interface:
        return None
    try:
        with open(f"/sys/class/net/{interface}/address", encoding="utf-8") as mac_file:
            return mac_file.read().strip()
    except FileNotFoundError:
        return None
    except Exception as e:
        LOGGER.warning("Unable to read MAC address for interface %s: %s", interface, e)
        return None


def _get_mac_details():
    # LƯU Ý THIẾT KẾ: Quét danh sách giao diện mạng ("eth0", "end0") là cấu hình phần cứng
    # mặc định và cố định của dòng thiết bị Javis Home Controller (HC).
    # Không cần quét các interface khác để đảm bảo tính nhất quán định danh thiết bị.
    for interface in ("eth0", "end0"):
        mac = _read_interface_mac(interface)
        if not mac:
            continue
        try:
            return _mac_to_decimal(mac), f"sysfs:{interface}", mac
        except ValueError as e:
            LOGGER.warning("Invalid MAC address from interface %s: %s", interface, e)

    raise RuntimeError("Unable to resolve Home Controller MAC from eth0 or end0")


def get_mac():
    mac_decimal, source, mac_address = _get_mac_details()
    LOGGER.info(
        "Resolved Home Controller MAC: decimal=%s mac=%s source=%s",
        mac_decimal,
        mac_address,
        source,
    )
    return mac_decimal

def yaml2dict(filename):
    try:
        if not os.path.exists(filename):
            with open(filename, 'w+', encoding='utf-8'):
                pass
        with open(filename, encoding='utf8') as file:
            return yaml.load(file, Loader=yaml.FullLoader)
    except Exception as e:
        LOGGER.error(f"Error loading YAML file {filename}: {e}")
        LOGGER.error(traceback.format_exc())
        return {}

def dict2yaml(dict_, filename):
    with open(filename, 'w', encoding='utf-8') as outfile:
        yaml.dump(dict_, outfile, default_flow_style=False, allow_unicode=True)
