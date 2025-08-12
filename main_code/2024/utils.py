from .const import *
import json
import os
from homeassistant.const import __version__ as ha_version
import logging
import uuid
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
        os.rename(PATH_PERSON_LOG, new_file_path)
    else:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            # convert to "%y%m%d"
            new_file_name = datetime.strptime(date_str, "%Y-%m-%d").strftime("%y%m%d") + ".log"
        except ValueError:
            LOGGER.error("Invalid date format. Use YYYY-MM-DD.")
            return
    new_file_path = FOLDER_PERSON_LOG + new_file_name
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
        mac = get_mac()
        base_url = f"https://{mac}.{add_url}"
    return base_url


def get_mac():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    mac_dec = int(mac, 16)
    return mac_dec

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