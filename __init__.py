"""The spotify integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import aiohttp

from .const import DOMAIN, SERVER_URL, PATH
import logging
import json
import os
LOGGER = logging.getLogger(__name__)

__all__ = [
    "DOMAIN"
]

def write_data(data):
    with open(PATH, "w", encoding='utf-8') as json_file:
        json.dump(data, json_file,ensure_ascii=False, indent=4)  # indent=4 for pretty formatting

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Spotify from a config entry."""
    token = entry.data.get("token")
    data = {"access_token": token.get("access_token")}
    info = None
    add_url = entry.data.get("url")

    async with aiohttp.ClientSession() as session:
        async with session.post(SERVER_URL + add_url + "/api/hanet/get_info", data=data) as response:
            info = await response.json()
            # write data

    if info:
        await hass.async_add_executor_job(write_data, info)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return True

