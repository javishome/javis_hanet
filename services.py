"""Services for javis_lock integration."""
"""Services for javis_lock integration."""

import logging
import voluptuous as vol
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse
    )
import homeassistant.helpers.config_validation as cv
from homeassistant.util.dt import as_utc

from .load_const import use_const

import traceback
import json
import os
import datetime
import aiohttp
_LOGGER = logging.getLogger(__name__)


class Services:
    """Wraps service handlers."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the service singleton."""
        self.hass = hass

    def register_old(self) -> None:
        """Register services for javis_lock integration."""
        #Tạo passcode
        self.hass.services.async_register(
            use_const.DOMAIN,
            use_const.SVC_WRITE_PERSON,
            self.handle_write_person,
            schema=vol.Schema(
                {
                    vol.Required("payload"): cv.string,
                }

            ) ,
            supports_response=SupportsResponse.OPTIONAL
            )
        
        self.hass.services.async_register(
            use_const.DOMAIN,
            use_const.SVC_PUSH_TO_QCD,
            self.change_face_log_name,
            vol.Schema(
                {
                    vol.Required("secret_key"): cv.string,
                }

            ),
            supports_response=SupportsResponse.OPTIONAL
        )

    def register_new(self) -> None:
        """Register services for javis_lock integration."""
        #Tạo passcode
        self.hass.services.register(
            use_const.DOMAIN,
            use_const.SVC_WRITE_PERSON,
            self.handle_write_person,
            schema=vol.Schema(
                {
                    vol.Required("payload"): cv.string,
                }

            ),
            supports_response=SupportsResponse.OPTIONAL
        )

        self.hass.register(
            use_const.DOMAIN,
            use_const.SVC_PUSH_TO_QCD,
            self.change_face_log_name,
            vol.Schema(
                {
                    vol.Required("secret_key"): cv.string,
                }

            ),
            supports_response=SupportsResponse.OPTIONAL
        )

    def handle_write_person(self, call: ServiceCall) -> ServiceResponse :
        """Handle the service call."""
        payload = call.data.get("payload")
        try:
            data = json.loads(payload)
            self.hass.add_job(write_data, data)
            return {"status": "ok"}
        except Exception as e:
            _LOGGER.error(traceback.format_exc())
            return {"status": "error", "message": str(e)}
    
    async def change_face_log_name(self, call: ServiceCall):

        secret_key = call.data.get("secret_key")
        try:
            self.hass.async_add_job(change_file_name, secret_key)
            return {"status": "ok"}
        except Exception as e:
            _LOGGER.error(traceback.format_exc())
            return {"status": "error", "message": str(e)}



def write_data( data):
    #check if folder exist
    if os.path.exists(use_const.FOLDER_PERSON_LOG) == False:
        os.makedirs(use_const.FOLDER_PERSON_LOG)
    #convert data to string and add to file
    with open(use_const.PATH_PERSON_LOG, "a", encoding='utf-8') as txt_file:
        txt_file.write(str(data) + "\n")

async def change_file_name(secret_key):
    #change name
    if os.path.exists(use_const.PATH_PERSON_LOG) == False:
        return
    new_file_name = datetime.datetime.now().strftime("%y%m%d") + ".log"
    new_file_path = use_const.FOLDER_PERSON_LOG + new_file_name
    os.rename(use_const.PATH_PERSON_LOG, new_file_path)

    qcd_url = "https://qcd.arrow-tech.vn/api/v2/resum-timesheet"
    headers = {
    "Content-Type": "application/json; charset=utf-8",
        "timesheet_secret_key": secret_key
    }
    payload = []
    with open(new_file_path, "r", encoding='utf-8') as txt_file:
        content = txt_file.read()
        for line in content.split("\n"):
            if line == "":
                continue
            line = line.replace("'", '"')
            data = json.loads(line)
            payload.append(data)

    async with aiohttp.ClientSession() as session:
        async with session.post(qcd_url, json=payload, headers = headers) as response:
            info = await response.json()
            if response.status != 200:
                _LOGGER.error(info)
                return False
