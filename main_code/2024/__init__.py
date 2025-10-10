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
import traceback
import pytz
import re
import time
from copy import deepcopy
LOGGER = logging.getLogger(__name__)

__all__ = ["DOMAIN"]


HANOI_TZ = pytz.timezone("Asia/Ho_Chi_Minh")
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
        start_time = time.time()
        account_type = entry.data.get("account_type")
        is_updated = False
        if account_type == "ai_box":
            is_updated = await update_data_ai_box(hass, entry)
        else:
            is_updated = await update_data_hanet(hass, entry)
        if not is_updated:
            LOGGER.error("Failed to update data")
            return False
        LOGGER.info(f"Data updated in {time.time() - start_time:.2f} seconds")
        hass.data.setdefault(DOMAIN, {})["entry"] = entry
    except Exception as e:
        LOGGER.error(f"Error setting up entry: {e}")
        LOGGER.error(traceback.format_exc())
        return False
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry):
    await hass.async_add_executor_job(remove_data)
    LOGGER.info(f"Removed data for entry {entry.entry_id}")
    return True
    
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    LOGGER.info(f"Unloading entry {entry.entry_id}")
    return True

async def async_get_options_flow(config_entry):
    account_type = config_entry.data.get("account_type")
    LOGGER.info(f"Getting options flow for account type: {account_type}")
    return HanetOptionsFlow(config_entry)

async def update_data_ai_box(hass, entry):
    ip = entry.data.get("ip")
    port = entry.data.get("port")
    key = entry.data.get("key")
    url = f"http://{ip}:{port}/api/Profile"
    headers = {
        "Cookie": f"key={key}"
    }
    info = {"person": []}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                LOGGER.error(f"Failed to fetch data from AI Box: {response.status}")
                return False
            data = await response.json()
            for person in data:
                new_person = {
                    "person_id": str(person.get("id")),
                    "person_type": None,
                    "image": "",
                    "person_name": person.get("name"),
                    "place_id": None,
                    "place_name": "",
                    }
                info["person"].append(new_person)
    if info:
        await hass.async_add_executor_job(write_data, info)
    return True

async def update_data_hanet(hass: HomeAssistant, entry):
    """Update data for the config entry."""
    token = entry.data.get("token")
    places = entry.options.get("selected_places", entry.data.get("selected_places", []))
    data = {"access_token": token.get("access_token"), "places": places}
    add_url = entry.data.get("url")
    old_data = await hass.async_add_executor_job(load_json_file, PATH)
    old_persons = old_data.get("person", [])

    old_by_id = {str(p.get("person_id")): p for p in old_persons if p.get("person_id") is not None}
    LOGGER.info("handle " + str(len(old_by_id)) + " old persons")


    async with aiohttp.ClientSession() as session:
        async with session.post(
            get_host(add_url) + "/api/hanet/get_info_with_places", json=data
        ) as response:
            info = await response.json()
            # add start_time and end_time to info
            if info and isinstance(info.get("person"), list):
                for person in info["person"]:
                    pid = str(person.get("person_id"))
                    #pop start_time and end_time if they exist
                    old_p = old_by_id.get(pid)
                    if old_p:
                        # giữ nguyên giá trị cũ (nếu có), tránh overwrite bằng None
                        if old_p.get("start_time"):
                            person["start_time"] = old_p.get("start_time")
                        if old_p.get("end_time"):
                            person["end_time"] = old_p.get("end_time")
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
    value_template_str = value_template_str.replace("''", "")

    value_template_str = value_template_str.replace("\"\"", "")
    value_template_str = value_template_str.replace(",,", ",")
    value_template_str = value_template_str.replace("[,", "[")
    value_template_str = value_template_str.replace("'", "\"")
    value_template_str = value_template_str.replace('"', "'")
    value_template_str = re.sub(r',\s*,', ',', value_template_str)
    value_template_str = re.sub(r'\[\s*,\s*', '[', value_template_str)
    value_template_str = re.sub(r',\s*\]', ']', value_template_str)

    return value_template_str



async def remove_expired_pids_from_face_sensor(expired_pids, hass):
    if not expired_pids:
        return
    if not os.path.exists(FACE_SENSOR_PATH):
        LOGGER.error(f"File {FACE_SENSOR_PATH} not found")
        return
    
    data_face_sensor = await hass.async_add_executor_job(yaml2dict, FACE_SENSOR_PATH)
    face_sensors = data_face_sensor.get("mqtt", {}).get("binary_sensor", [])
    
    for sensor in face_sensors:
        value_template = sensor.get("value_template", "")
        if value_template:
            for pid in expired_pids:
                if str(pid) in value_template:
                    value_template = remove_person_id_in_value_template(pid, value_template)
            last_value_template = deepcopy(value_template)
            for i in range(1000):
                value_template =  tuning_value_template(value_template)
                if value_template == last_value_template:
                    break
                last_value_template = value_template
            sensor["value_template"] = last_value_template
    
    await hass.async_add_executor_job(dict2yaml, data_face_sensor, FACE_SENSOR_PATH)



def load_json_file(path):
    """Đọc file JSON và trả về dữ liệu"""
    if not os.path.exists(path):
        LOGGER.info(f"❌ File không tồn tại: {path}")
        LOGGER.info("Tạo file mới")
        return {}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                LOGGER.error("⚠️ File rỗng")
                return {}
            return json.loads(content)
    except Exception as e:
        LOGGER.error(f"❌ Lỗi đọc JSON: {e}")
        return None


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

    # Define timezone for Hanoi

    now_in_hanoi = datetime.now(HANOI_TZ)
    now_in_hanoi_naive = now_in_hanoi.replace(tzinfo=None).date()
    LOGGER.info(f"Current time in Hanoi: {now_in_hanoi_naive}")
    expired_pids = []
    for item in persons:
        end_str = item.get("end_time")
        person_id = item.get("person_id")

        try:
            end_time = datetime.strptime(end_str, "%Y-%m-%d").date() if end_str else None
        except ValueError as e:
            LOGGER.warning(f"Invalid datetime format in item {item}: {e}")
            continue

        # Điều kiện giữ lại người dùng là từ ngày bắt đầu tới trước ngày kết thúc
        if end_time:
            if  now_in_hanoi_naive >= end_time:
                expired_pids.append(person_id)

    # Xóa người không hợp lệ
    await remove_expired_pids_from_face_sensor(expired_pids, hass)
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

async def update_period_api(start_time, end_time, person_id):
    url = f"{HRM_URL}/api/v2/update_period"
    headers = {
        "Content-Type": "application/json",
        "timesheet_secret_key": TIMESHEET_SECRET_KEY
    }
    data = {
        "start_time": start_time,
        "end_time": end_time,
        "person_id": person_id
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                LOGGER.info(f"Period updated successfully for person_id {person_id} with start_time {start_time} and end_time {end_time}")
            else:
                LOGGER.error(f"Failed to update period: {response.status}")


async def sync_periods_api(hass: HomeAssistant):
    url = f"{HRM_URL}/api/v2/sync_periods"
    headers = {
        "Content-Type": "application/json",
        "timesheet_secret_key": TIMESHEET_SECRET_KEY
    }
    person_data = await hass.async_add_executor_job(load_json_file, PATH)
    person = person_data.get("person", [])
    data = [{
        "person_id": p.get("person_id"),
        "start_time": p.get("start_time"),
        "end_time": p.get("end_time")
    } for p in person if p.get("person_id")]
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                LOGGER.info("Periods synced successfully.")
                return True
            else:
                LOGGER.error(f"Failed to sync periods: {response.status}")
                return False

def flexible_date(value):
    """Chấp nhận None, chuỗi rỗng, khoảng trắng hoặc date hợp lệ."""
    if value is None:
        return None
    if isinstance(value, str):
        val = value.strip()
        if val == "":
            return None
        try:
            return cv.date(val)  # parse chuỗi thành date hợp lệ
        except Exception:
            raise vol.Invalid(f"Invalid date: {value}")
    # Nếu đã là datetime/date
    try:
        return cv.date(value)
    except Exception:
        raise vol.Invalid(f"Invalid date: {value}")
    
                 
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
                    vol.Optional("date"): cv.date,  # Optional date to specify which log file to change
                }
            ),
            supports_response=SupportsResponse.OPTIONAL,
        )
        self.hass.services.async_register(
            DOMAIN,
            SVC_UPDATE_PERIOD,
            self.update_period,
            schema=vol.Schema(
                {
                    vol.Optional("start_time"): flexible_date,
                    vol.Optional("end_time"): flexible_date,
                    vol.Required("person_id"): cv.string,
                }
            ),
            supports_response=SupportsResponse.OPTIONAL,
        )

        self.hass.services.async_register(
            DOMAIN,
            SVC_CHECK_FACEID_GROUP_SENSOR,
            self.check_faceid_group_sensor,
            supports_response=SupportsResponse.OPTIONAL,
        )
        self.hass.services.async_register(
            DOMAIN,
            SVC_SYNC_PERIODS,
            self.sync_periods,
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
                    vol.Optional("date"): cv.date, # Optional date to specify which log file to change
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
                    vol.Optional("start_time"): flexible_date,
                    vol.Optional("end_time"): flexible_date,
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

        self.hass.services.register(
            DOMAIN,
            SVC_SYNC_PERIODS,
            self.sync_periods,
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
        start_time = time.time()
        await handle_person_data(self.hass)
        end_time = time.time()
        LOGGER.info(f"Checked faceID group sensor in {end_time - start_time:.2f} seconds")
        return {"status": "ok", "message": "FaceID group sensor checked and updated."}

    async def change_face_log_name(self, call: ServiceCall):
        secret_key = call.data.get("secret_key")
        date = call.data.get("date")
        if date:
            date_str = date.strftime("%Y-%m-%d")
        try:
            self.hass.async_create_task(change_file_name(secret_key, date_str))
            return {"status": "ok"}
        except Exception as e:
            LOGGER.error(traceback.format_exc())
            return {"status": "error", "message": str(e)}
        
    async def update_period(self, call: ServiceCall):
        """Handle the update period service call."""
        # Implement the logic for updating the period
        start_time = call.data.get("start_time")
        end_time = call.data.get("end_time")
        person_id = call.data.get("person_id")
        #nếu start_time >= end_time thì trả về lỗi
        # if start_time >= end_time:
        #     return {"status": "error", "message": "Start time must be less than end time"}
        #conver start_time and end_time to string
        start_time_str = ""
        if start_time:
            start_time_str = start_time.strftime("%Y-%m-%d")
        end_time_str = ""
        if end_time:
            end_time_str = end_time.strftime("%Y-%m-%d")
        # start_time = start_time.strftime("%Y-%m-%d")
        # end_time = end_time.strftime("%Y-%m-%d")
        

        # read file person_javis_v2.json
        data = await self.hass.async_add_executor_job(load_json_file, PATH)
        persons = data.get("person", [])
        # find person with person_id
        person = next((p for p in persons if p.get("person_id") == person_id), None)
        if not person:
            return {"status": "error", "message": f"Person with ID {person_id} not found"}
        else:
            # update start_time and end_time
            person["start_time"] = start_time_str
            person["end_time"] = end_time_str
            # save data to file
            await self.hass.async_add_executor_job(save_json_file, PATH, data)
            # kiêm tra xem thời gian hiên tại có nằm trong khoảng thời gian của người dùng không
            now_in_hanoi = datetime.now(HANOI_TZ)
            now_in_hanoi_naive = now_in_hanoi.replace(tzinfo=None).date()
            if end_time:
                if now_in_hanoi_naive >= end_time:
                    # remove person_id in face_sensor.yaml
                    await remove_expired_pids_from_face_sensor([person_id], self.hass)
                    await restart_mqtt(self.hass)
                # update period in HRM
            await update_period_api(start_time_str, end_time_str, person_id)
        return {"status": "ok", "message": f"Updated period"}


    async def sync_periods(self, call: ServiceCall):
        """Handle the sync periods service call."""
        try:
            is_sync = await sync_periods_api(self.hass)
            if not is_sync:
                return {"status": "error", "message": "Failed to sync periods."}
            return {"status": "ok", "message": "Periods synced successfully."}
        except Exception as e:
            LOGGER.error(f"Error syncing periods: {e}")
            return {"status": "error", "message": str(e)}



