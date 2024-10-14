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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Spotify from a config entry."""
    token = entry.data.get("token")
    data = {"access_token": token.get("access_token")}
    info = None

    async with aiohttp.ClientSession() as session:
        async with session.post(SERVER_URL + "/get_info", data=data) as response:
            info = await response.json()
            # write data

    if info:
        
        with open(PATH, "w", encoding='utf-8') as json_file:
            json.dump(info, json_file,ensure_ascii=False, indent=4)  # indent=4 for pretty formatting
    else:
        LOGGER.error("Failed to get info from server")

    return True

