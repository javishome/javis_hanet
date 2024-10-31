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

    def handle_write_person(self, call: ServiceCall) -> ServiceResponse :
        """Handle the service call."""
        payload = call.data.get("payload")
        _LOGGER.info("payload: %s", payload)
        try:
            data = json.loads(payload)
            self.hass.add_job(write_data, data)
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