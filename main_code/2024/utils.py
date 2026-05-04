from .const import *
import json
import os
from homeassistant.const import __version__ as ha_version
import logging
import uuid
import subprocess
import urllib.request
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
    if os.path.exists(FOLDER_PERSON_LOG) == False:
        os.makedirs(FOLDER_PERSON_LOG)
    # convert data to string and add to file
    with open(PATH_PERSON_LOG, "a", encoding="utf-8") as txt_file:
        txt_file.write(str(data) + "\n")


async def change_file_name(secret_key, date_str=None):
    # change name
    if not date_str:
        if os.path.exists(PATH_PERSON_LOG) == False:
            return
        new_file_name = datetime.now().strftime("%y%m%d") + ".log"
    else:
        try:
            new_file_name = datetime.strptime(date_str, "%Y-%m-%d").strftime("%y%m%d") + ".log"
        except ValueError:
            LOGGER.error("Invalid date format. Use YYYY-MM-DD.")
            return
    new_file_path = FOLDER_PERSON_LOG + new_file_name
    os.rename(PATH_PERSON_LOG, new_file_path)
    if not os.path.exists(new_file_path):
        LOGGER.error(f"File {new_file_path} does not exist.")
        return False
    

    qcd_url = "https://qcd.arrow-tech.vn/api/v2/resum-timesheet"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "timesheet_secret_key": secret_key,
    }
    payload = []
    with open(new_file_path, "r", encoding="utf-8") as txt_file:
        content = txt_file.read()
        for line in content.split("\n"):
            if line == "":
                continue
            line = line.replace("'", '"')
            data = json.loads(line)
            payload.append(data)

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


def _find_mac_in_supervisor_interface(interface):
    for key in ("mac", "mac_address", "macaddress", "hw_address"):
        value = interface.get(key)
        if value:
            return value
    return None


def _interface_name(interface):
    return str(
        interface.get("interface")
        or interface.get("name")
        or ""
    ).lower()


def _get_supervisor_device_mac():
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        return None

    request = urllib.request.Request(
        "http://supervisor/network/info",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        LOGGER.warning("Unable to read Supervisor network info: %s", e)
        return None

    interfaces = payload.get("data", {}).get("interfaces", [])
    if not isinstance(interfaces, list):
        return None

    for interface in interfaces:
        if isinstance(interface, dict) and _interface_name(interface) == "eth0":
            mac = _find_mac_in_supervisor_interface(interface)
            if mac:
                return mac, "supervisor:eth0"

    for interface in interfaces:
        if isinstance(interface, dict):
            if interface.get("primary"):
                mac = _find_mac_in_supervisor_interface(interface)
                if mac:
                    return mac, f"supervisor:{_interface_name(interface) or 'primary'}"

    for interface in interfaces:
        if isinstance(interface, dict):
            mac = _find_mac_in_supervisor_interface(interface)
            if mac:
                return mac, f"supervisor:{_interface_name(interface) or 'unknown'}"
    return None


def _get_default_route_interface():
    try:
        output = subprocess.check_output(
            ["ip", "route", "get", "1.1.1.1"],
            stderr=subprocess.DEVNULL,
            timeout=3,
        ).decode("utf-8", errors="ignore")
    except Exception as e:
        LOGGER.warning("Unable to determine default route interface: %s", e)
        return None

    parts = output.split()
    if "dev" not in parts:
        return None
    dev_index = parts.index("dev") + 1
    if dev_index >= len(parts):
        return None
    return parts[dev_index]


def _read_interface_mac(interface):
    if not interface:
        return None
    try:
        with open(f"/sys/class/net/{interface}/address", "r", encoding="utf-8") as mac_file:
            return mac_file.read().strip()
    except Exception as e:
        LOGGER.warning("Unable to read MAC address for interface %s: %s", interface, e)
        return None


def _read_eth0_mac():
    mac = _read_interface_mac("eth0")
    if not mac:
        return None
    return mac, "sysfs:eth0"


def _get_mac_details():
    supervisor_mac = _get_supervisor_device_mac()
    if supervisor_mac:
        mac, source = supervisor_mac
        try:
            return _mac_to_decimal(mac), source, mac
        except ValueError as e:
            LOGGER.warning("Invalid MAC address from %s: %s", source, e)

    eth0_mac = _read_eth0_mac()
    if eth0_mac:
        mac, source = eth0_mac
        try:
            return _mac_to_decimal(mac), source, mac
        except ValueError as e:
            LOGGER.warning("Invalid MAC address from %s: %s", source, e)

    interface = _get_default_route_interface()
    mac = _read_interface_mac(interface)
    if mac:
        try:
            return _mac_to_decimal(mac), f"sysfs:{interface}", mac
        except ValueError as e:
            LOGGER.warning("Invalid MAC address from interface %s: %s", interface, e)

    mac_hex = uuid.UUID(int=uuid.getnode()).hex[-12:]
    mac_address = ":".join(mac_hex[i:i+2] for i in range(0, 12, 2))
    return int(mac_hex, 16), "uuid.getnode", mac_address


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
        exist = os.path.exists(filename)
        if not exist:
            f = open(filename, 'w+')
            f.close()
        file = open(filename, 'r', encoding='utf8')
        res = yaml.load(file, Loader=yaml.FullLoader)
        file.close()
        return res
    except Exception as e:
        LOGGER.error(f"Error loading YAML file {filename}: {e}")
        LOGGER.error(traceback.format_exc())
        return {}
    
def dict2yaml(dict_, filename):
    with open(filename, 'w', encoding='utf-8') as outfile:
        yaml.dump(dict_, outfile, default_flow_style=False, allow_unicode=True)
