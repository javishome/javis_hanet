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
LOGGER = logging.getLogger(__name__)

__all__ = ["DOMAIN"]


def setup(hass: HomeAssistant, config: ConfigEntry) -> bool:
    """Set up the TTLock component."""
    if is_new_version():
        Services(hass).register_new()
    else:
        Services(hass).register_old()

    return True




async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Spotify from a config entry."""
    token = entry.data.get("token")
    places = entry.options.get("selected_places", entry.data.get("selected_places", []))
    data = {"access_token": token.get("access_token"), "places": places}
    info = None
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


