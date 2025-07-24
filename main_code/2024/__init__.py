"""The spotify integration."""

from __future__ import annotations
import uuid

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import aiohttp
import logging
import json
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
import homeassistant.helpers.config_validation as cv
import traceback
from .config_flow import HanetOptionsFlow
from .const import *
from .utils import *
import re
from datetime import timedelta
from homeassistant.helpers.event import async_track_point_in_time
import yaml
import traceback

LOGGER = logging.getLogger(__name__)

__all__ = ["DOMAIN"]


def setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the TTLock component."""
    if is_new_version():
        Services(hass).register_new()
    else:
        Services(hass).register_old()
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Spotify from a config entry."""
    try:
        await update_data(hass, entry)
        await schedule_daily_update(hass)
        await handle_person_data(hass)
        hass.data.setdefault(DOMAIN, {})["entry"] = entry
    except Exception as e:
        LOGGER.error(f"Error setting up entry: {e}")
        LOGGER.error(traceback.format_exc())
        return False
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    token = entry.data.get("token")
    places = entry.options.get("selected_places", entry.data.get("selected_places", []))
    data = {"access_token": token.get("access_token"), "places": places}
    add_url = entry.data.get("url")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            get_host(add_url) + "/api/hanet/get_info_with_places", json=data
        ) as response:
            info = await response.json()
            if response.status != 200:
                LOGGER.error(info)
            else:
                await hass.async_add_executor_job(remove_data)
    return True

async def async_get_options_flow(config_entry):
    return HanetOptionsFlow(config_entry)


async def schedule_daily_update(hass: HomeAssistant):
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    target_time = datetime(
        year=tomorrow.year,
        month=tomorrow.month,
        day=tomorrow.day,
        hour=0,
        minute=30,
        second=0,
        tzinfo=now.tzinfo  # đảm bảo sử dụng đúng timezone của hệ thống
    )

    async def run_and_reschedule(now_time):
        await handle_person_data(hass)   # gọi hàm cập nhật của bạn
        await schedule_daily_update(hass)  # tự lên lịch lại cho ngày hôm sau

    async_track_point_in_time(hass, run_and_reschedule, target_time)


async def update_data(hass: HomeAssistant, entry):
    """Update data for the config entry."""
    token = entry.data.get("token")
    places = entry.options.get("selected_places", entry.data.get("selected_places", []))
    data = {"access_token": token.get("access_token"), "places": places}
    add_url = entry.data.get("url")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            get_host(add_url) + "/api/hanet/get_info_with_places", json=data
        ) as response:
            info = await response.json()
            if response.status != 200:
                LOGGER.error(info)
                return False
            # write data

    if info:
        await hass.async_add_executor_job(write_data, info)
    

    return True

def remove_person_id_in_value_template(person_id_to_remove, value_template_str):
    value_template_str = value_template_str.strip()
    value_template_str = value_template_str.replace(person_id_to_remove, "")
    return value_template_str

def tuning_value_template(value_template_str):
    value_template_str = value_template_str.strip()
    value_template_str = value_template_str.replace("\"\"", "")
    value_template_str = value_template_str.replace(",,", ",")
    value_template_str = value_template_str.replace("[,", "[")
    value_template_str = value_template_str.replace("'", "\"")
    value_template_str = value_template_str.replace('"', "'")
    return value_template_str



async def remove_data_in_face_sensor(person_id, hass: HomeAssistant):
    """Remove person data from face sensor."""
    if not os.path.exists(FACE_SENSOR_PATH):
        LOGGER.error(f"File {FACE_SENSOR_PATH} not found")
        return {}
    data_face_sensor = await hass.async_add_executor_job(yaml2dict, FACE_SENSOR_PATH)
    if data_face_sensor and data_face_sensor.get("mqtt") and data_face_sensor.get("mqtt").get("binary_sensor"):
        face_sensors = data_face_sensor.get("mqtt").get("binary_sensor")
        for sensor in face_sensors:
            value_template = sensor.get("value_template")
            if value_template and str(person_id) in value_template:
                sensor["value_template"] = remove_person_id_in_value_template(person_id, value_template)
                LOGGER.info(f"Updated value_template for sensor {sensor.get('name')}: {sensor['value_template']}")
            sensor["value_template"] = tuning_value_template(sensor["value_template"])
        # save the updated data back to the file
        await hass.async_add_executor_job(dict2yaml, data_face_sensor, FACE_SENSOR_PATH)



def load_json_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}  # file rỗng, trả về dict rỗng để không lỗi
            return json.loads(content)
    except Exception as e:
        LOGGER.error(f"Error loading JSON file {path}: {e}")
        return {}

def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def handle_person_data(hass: HomeAssistant):
    if not os.path.exists(PATH):
        return

    data = await hass.async_add_executor_job(load_json_file, PATH)


    persons = data.get("person", [])
    if not persons:
        return

    now = datetime.now()

    for item in persons:
        start_str = item.get("start_time")
        end_str = item.get("end_time")
        person_id = item.get("person_id")

        try:
            start_time = datetime.strptime(start_str, "%Y-%m-%d") if start_str else None
            end_time = datetime.strptime(end_str, "%Y-%m-%d") if end_str else None
        except ValueError as e:
            LOGGER.warning(f"Invalid datetime format in item {item}: {e}")
            continue

        # Điều kiện giữ lại người dùng là từ ngày bắt đầu tới trước ngày kết thúc
        if start_time and end_time:
            if start_time <= now < end_time:
                continue

            LOGGER.info(f"Removing person {person_id} with start_time {start_str} and end_time {end_str} as it is not in the valid period.")
            # Xóa người không hợp lệ
            await remove_data_in_face_sensor(person_id, hass)
    # reload mqtt
    await restart_mqtt(hass)

async def restart_mqtt(hass: HomeAssistant):
    secret_file = os.path.join(PATH_CONFIG, 'secrets.yaml')
    url_service = f'http://localhost:8123/api/services/mqtt/reload'
    data = await hass.async_add_executor_job(yaml2dict, secret_file)
    authen_code = data['token']
    headers = {
        "Authorization": "Bearer " + authen_code,
        "content-type": "application/json"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url_service, headers=headers) as response:
            if response.status == 200:
                LOGGER.info("MQTT service reloaded successfully.")
            else:
                LOGGER.error(f"Failed to reload MQTT service: {response.status}")
            
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

        self.hass.services.register(
            DOMAIN,
            SVC_UPDATE_PERIOD,
            self.update_period,
            schema=vol.Schema(
                {
                    vol.Required("start_time"): cv.date,
                    vol.Required("end_time"): cv.date,
                    vol.Required("person_id"): cv.string,
                }
            ),
            supports_response=SupportsResponse.OPTIONAL,
        )

        self.hass.services.register(
            DOMAIN,
            SVC_DELETE_PERIOD,
            self.delete_period,
            schema=vol.Schema(
                {
                    vol.Required("person_id"): cv.string,
                }
            ),
            supports_response=SupportsResponse.OPTIONAL,
        )

        self.hass.services.register(
            DOMAIN,
            SVC_CHECK_FACEID_GROUP_SENSOR,
            self.check_faceid_group_sensor,
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
        
    async def check_faceid_group_sensor(self, call: ServiceCall):
        """Handle the check faceid group sensor service call."""
        await handle_person_data(self.hass)

    async def change_face_log_name(self, call: ServiceCall):
        secret_key = call.data.get("secret_key")
        try:
            self.hass.async_add_job(change_file_name, secret_key)
            return {"status": "ok"}
        except Exception as e:
            LOGGER.error(traceback.format_exc())
            return {"status": "error", "message": str(e)}
        
    async def update_period(self, call: ServiceCall):
        """Handle the update period service call."""
        # Implement the logic for updating the period
        start_time = call.data.get("start_time")
        end_time = call.data.get("end_time")
        #nếu start_time >= end_time thì trả về lỗi
        if start_time >= end_time:
            return {"status": "error", "message": "Start time must be less than end time"}
        #conver start_time and end_time to string
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")

        person_id = call.data.get("person_id")
        endpoint = "/api/hanet/save_period"
        # get the token from the config entry
        entry = self.hass.data.get(DOMAIN, {}).get("entry")
        if not entry:
            LOGGER.error("Missing config entry in hass.data")
            return {"status": "error", "message": "Missing config entry"}

        token = entry.data.get("token", {}).get("access_token")
        add_url = entry.data.get("url")
        data = {
            "start_time": start_time,
            "end_time": end_time,
            "person_id": person_id,
            "access_token": token
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                get_host(add_url) + endpoint, json=data
            ) as response:
                info = await response.json()
                if response.status != 200:
                    LOGGER.error(info)
                    return {"status": "error", "message": info}
                await update_data(self.hass, entry)
                await handle_person_data(self.hass)
                return {"status": "ok", "message": info}
            
    async def delete_period(self, call: ServiceCall):
        """Handle the delete period service call."""
        # Implement the logic for deleting the period
        person_id = call.data.get("person_id")
        endpoint = "/api/hanet/delete_period"
        # get the token from the config entry
        entry = self.hass.data.get(DOMAIN, {}).get("entry")
        if not entry:
            LOGGER.error("Missing config entry in hass.data")
            return {"status": "error", "message": "Missing config entry"}

        token = entry.data.get("token", {}).get("access_token")
        add_url = entry.data.get("url")
        data = {
            "person_id": person_id,
            "access_token": token
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                get_host(add_url) + endpoint, json=data
            ) as response:
                info = await response.json()
                if response.status != 200:
                    LOGGER.error(info)
                    return {"status": "error", "message": info}
                await update_data(self.hass, entry)
                await handle_person_data(self.hass)
                return {"status": "ok", "message": info}


