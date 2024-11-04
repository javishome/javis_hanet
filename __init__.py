"""The spotify integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import aiohttp
from .services import Services
from .load_const import use_const
import logging
import json
import os
from .utils import get_host
from homeassistant.const import __version__ as ha_version

LOGGER = logging.getLogger(__name__)

__all__ = [
    "DOMAIN"
]

def write_data(data):
    with open(use_const.PATH, "w", encoding='utf-8') as json_file:
        json.dump(data, json_file,ensure_ascii=False, indent=4)  # indent=4 for pretty formatting

def remove_data():
    if os.path.exists(use_const.PATH):
        os.remove(use_const.PATH)


def setup(hass: HomeAssistant, config: ConfigEntry) -> bool:
    """Set up the TTLock component."""
    if is_new_version():
        Services(hass).register_new()
    else:
        Services(hass).register_old()

    return True

def is_new_version():
    year,version = ha_version.split('.')[:2]
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
        async with session.post(get_host(use_const.SERVER_URL, add_url) + "/api/hanet/get_info", data=data) as response:
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
        async with session.post(get_host(use_const.SERVER_URL, add_url) + "/api/hanet/get_info", data=data) as response:
            info = await response.json()
            if response.status != 200:
                LOGGER.error(info)
            else:
                await hass.async_add_executor_job(remove_data)
    return True

