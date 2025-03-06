"""The spotify integration."""

from __future__ import annotations
import uuid

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import aiohttp
import logging
import json
import os
from homeassistant.const import __version__ as ha_version
from datetime import datetime
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
import homeassistant.helpers.config_validation as cv
import traceback

LOGGER = logging.getLogger(__name__)

# defind config
# common
DOMAIN = "javis_hanet"
HOST1 = "javisco.com"
HOST2 = "javishome.io"
HOST3 = "javiscloud.com"
CLIENT_ID = "94414a66f3c6a7e2ceadc17af8ccdd60"
CLIENT_SECRET = "secret"
AUTHORIZE_URL = "https://oauth.hanet.com/oauth2/authorize"
SVC_WRITE_PERSON = "write_person"
SVC_PUSH_TO_QCD = "push_to_qcd"

# 1 prod
SERVER_URL = "https://lock-api."
PATH_CONFIG = "/config/"
MODE = "prod"

# # 2 dev (server test and ha test)
# SERVER_URL = "https://improved-liger-tops.ngrok-free.app"
# PATH_CONFIG = os.getcwd() + "/config/"
# MODE = "dev"
# #3 real dev (for server test on ha real)
# SERVER_URL = "https://improved-liger-tops.ngrok-free.app"
# PATH_CONFIG = "/config/"
# MODE = "dev_ha_real"
# common
PATH = PATH_CONFIG + "person_javis_v2.json"
FOLDER_PERSON_LOG = PATH_CONFIG + "timesheet/"
PATH_PERSON_LOG = FOLDER_PERSON_LOG + "timesheet.log"


__all__ = ["DOMAIN"]


def write_data(data):
    with open(PATH, "w", encoding="utf-8") as json_file:
        json.dump(
            data, json_file, ensure_ascii=False, indent=4
        )  # indent=4 for pretty formatting


def remove_data():
    if os.path.exists(PATH):
        os.remove(PATH)


def setup(hass: HomeAssistant, config: ConfigEntry) -> bool:
    """Set up the TTLock component."""
    if is_new_version():
        Services(hass).register_new()
    else:
        Services(hass).register_old()

    return True


def is_new_version():
    year, version = ha_version.split(".")[:2]
    if int(year) >= 2024 and int(version) >= 7:
        return True
    return False


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Spotify from a config entry."""
    token = entry.data.get("token")
    data = {"access_token": token.get("access_token")}
    info = None
    add_url = entry.data.get("url")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            get_host(add_url) + "/api/hanet/get_info", data=data
        ) as response:
            info = await response.json()
            if response.status != 200:
                LOGGER.error(info)
                return False
            # write data

    if info:
        await hass.async_add_executor_job(write_data, info)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    token = entry.data.get("token")
    data = {"access_token": token.get("access_token")}
    add_url = entry.data.get("url")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            get_host(add_url) + "/api/hanet/get_info", data=data
        ) as response:
            info = await response.json()
            if response.status != 200:
                LOGGER.error(info)
            else:
                await hass.async_add_executor_job(remove_data)
    return True


class Services:
    """Wraps service handlers."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the service singleton."""
        self.hass = hass

    def register_old(self) -> None:
        """Register services for javis_lock integration."""
        # Tạo passcode
        self.hass.services.async_register(
            DOMAIN,
            SVC_WRITE_PERSON,
            self.handle_write_person,
            schema=vol.Schema(
                {
                    vol.Required("payload"): cv.string,
                }
            ),
            supports_response=SupportsResponse.OPTIONAL,
        )

        self.hass.services.async_register(
            DOMAIN,
            SVC_PUSH_TO_QCD,
            self.change_face_log_name,
            vol.Schema(
                {
                    vol.Required("secret_key"): cv.string,
                }
            ),
            supports_response=SupportsResponse.OPTIONAL,
        )

    def register_new(self) -> None:
        """Register services for javis_lock integration."""
        # Tạo passcode
        self.hass.services.register(
            DOMAIN,
            SVC_WRITE_PERSON,
            self.handle_write_person,
            schema=vol.Schema(
                {
                    vol.Required("payload"): cv.string,
                }
            ),
            supports_response=SupportsResponse.OPTIONAL,
        )

        self.hass.services.register(
            DOMAIN,
            SVC_PUSH_TO_QCD,
            self.change_face_log_name,
            vol.Schema(
                {
                    vol.Required("secret_key"): cv.string,
                }
            ),
            supports_response=SupportsResponse.OPTIONAL,
        )

    def handle_write_person(self, call: ServiceCall):
        """Handle the service call."""
        payload = call.data.get("payload")
        try:
            data = json.loads(payload)
            self.hass.add_job(write_data_log_qcd, data)
            return {"status": "ok"}
        except Exception as e:
            LOGGER.error(traceback.format_exc())
            return {"status": "error", "message": str(e)}

    async def change_face_log_name(self, call: ServiceCall):
        secret_key = call.data.get("secret_key")
        try:
            self.hass.async_add_job(change_file_name, secret_key)
            return {"status": "ok"}
        except Exception as e:
            LOGGER.error(traceback.format_exc())
            return {"status": "error", "message": str(e)}


def write_data_log_qcd(data):
    # check if folder exist
    if os.path.exists(FOLDER_PERSON_LOG) == False:
        os.makedirs(FOLDER_PERSON_LOG)
    # convert data to string and add to file
    with open(PATH_PERSON_LOG, "a", encoding="utf-8") as txt_file:
        txt_file.write(str(data) + "\n")


async def change_file_name(secret_key):
    # change name
    if os.path.exists(PATH_PERSON_LOG) == False:
        return
    new_file_name = datetime.now().strftime("%y%m%d") + ".log"
    new_file_path = FOLDER_PERSON_LOG + new_file_name
    os.rename(PATH_PERSON_LOG, new_file_path)

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
        mac = get_mac()
        base_url = f"https://{mac}.{add_url}"
    return base_url


def get_mac():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    mac_dec = int(mac, 16)
    return mac_dec
