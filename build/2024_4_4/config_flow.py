"""Config flow for Spotify."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any, Dict, cast

from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlowResult
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.const import  CONF_URL
from homeassistant import config_entries
import time
import asyncio
from http import HTTPStatus
from homeassistant.components.application_credentials import AuthImplementation
from homeassistant.components.application_credentials import ClientCredential
from homeassistant.components.application_credentials import AuthorizationServer
from homeassistant.loader import async_get_application_credentials
from homeassistant.components import http
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from json import JSONDecodeError
from homeassistant.helpers.network import NoURLAvailableError
from yarl import URL
from .const import *
from .utils import *
OAUTH_AUTHORIZE_URL_TIMEOUT_SEC = 30


OAUTH_TOKEN_TIMEOUT_SEC = 30

LOGGER = logging.getLogger(__name__)
AUTH_SCHEMA = vol.Schema(
    {
     vol.Required(CONF_URL, default=HOST3): vol.In(
                    [HOST1, HOST2, HOST3]
                )}
)

class HanetFlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Spotify OAuth2 authentication."""

    DOMAIN = DOMAIN
    VERSION = 1
    add_url = ""

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create an entry for Hanet with user-selected places."""
        await self.async_set_unique_id(data["token"]["userID"])

        # Gọi API lấy places
        session = async_get_clientsession(self.hass)
        self.logger.info("data: %s", data)
        body_data = {
            "access_token": data["token"]["access_token"],
        }
        try:
            async with session.post(get_host(self.add_url) + API_GET_PLACES_INFO_URL, data = body_data) as response:
                if response.status == HTTPStatus.OK:
                    places_info = await response.json()
                    data["places_info"] = places_info
                else:
                    LOGGER.error("Failed to fetch places info: %s", response.status)
                    return self.async_abort(reason="fetch_places_info_failed")
        except Exception as e:
            LOGGER.error("Error fetching places info: %s", str(e))
            return self.async_abort(reason="places_info_not_found")

        if not data["places_info"]:
            return self.async_abort(reason="no_places_info_available")

        # Lưu dữ liệu tạm để step tiếp theo dùng
        self.places_info = data["places_info"]
        self.token_data = data  # Giữ token + places
        self.logger.info("Token data: %s", self.token_data)

        return await self.async_step_select_places()
    
    async def async_step_select_places(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let user select places."""

        errors = {}

        places_dict = {
            str(place["place_id"]): place["place_name"] for place in self.places_info
        }
        schema = vol.Schema({
            vol.Required("selected_places"): cv.multi_select(places_dict)
        })


        if user_input is not None:
            selected = user_input["selected_places"]
            if not selected:
                errors["base"] = "no_place_selected"
                return self.async_show_form(
                    step_id="select_places",
                    data_schema=schema,
                    errors=errors,
                )
            
            self.logger.info("Selected places: %s", selected)
            
            selected_places = [
                place for place in self.places_info if str(place["place_id"]) in selected]

            # Ghi vào token_data để lưu
            self.token_data["selected_places"] = selected_places

            # Bỏ places_info để không ghi thừa trong config entry
            del self.token_data["places_info"]

            self.logger.info("Token data after selection: %s", self.token_data)

            return self.async_create_entry(
                title=self.token_data["token"]["email"],
                data=self.token_data,
            )

        return self.async_show_form(
            step_id="select_places",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Perform reauth upon migration of old entries."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauth dialog."""
        errors: Dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()
        errors["base"] = "reauth_failed"
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                description_placeholders={"account": reauth_entry.data["userID"]},
                errors=errors,
            )

    async def async_step_creation(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create config entry from external data."""
        self.logger.info("Creating config entry from external data")
        session = async_get_clientsession(self.hass)
        data = {
            "grant_type": "authorization_code",
            "code": self.external_data["code"],
            "redirect_uri": self.external_data["state"]["redirect_uri"],
        }

        try:
            async with asyncio.timeout(OAUTH_TOKEN_TIMEOUT_SEC):
                resp = await session.post(self.flow_impl.token_url, data=data)
                if resp.status >= 400:
                    try:
                        error_response = await resp.json()
                    except (Exception, JSONDecodeError):
                        error_response = {}
                    error_code = error_response.get("error", "unknown")
                    error_description = error_response.get(
                        "error_description", "unknown error"
                    )
                    LOGGER.error(
                        "Token request for %s failed (%s): %s",
                        self.domain,
                        error_code,
                        error_description,
                    )
                resp.raise_for_status()
                token = cast(dict, await resp.json())
        except TimeoutError as err:
            LOGGER.error("Timeout resolving OAuth token: %s", err)
            return self.async_abort(reason="oauth_timeout")
        except Exception as err:
            LOGGER.error("Error resolving OAuth token: %s", err)
            if (
                isinstance(err, Exception)
                and err.status == HTTPStatus.UNAUTHORIZED
            ):
                return self.async_abort(reason="oauth_unauthorized")
            return self.async_abort(reason="oauth_failed")

        if "expire" not in token:
            LOGGER.warning("Invalid token: %s", token)
            return self.async_abort(reason="oauth_error")

        # Force int for non-compliant oauth2 providers
        try:
            token["expire"] = int(token["expire"])
        except ValueError as err:
            LOGGER.warning("Error converting expire to int: %s", err)
            return self.async_abort(reason="oauth_error")
        token["expires_at"] = time.time() + token["expire"]

        self.logger.info("Successfully authenticated")

        return await self.async_oauth_create_entry(
            {"auth_implementation": self.flow_impl.domain, "token": token, "url": self.add_url}
        )

    async def async_step_pick_implementation(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Handle a flow start."""

        if  user_input:
            self.add_url = user_input[CONF_URL]
            url = get_host(self.add_url) + "/api/hanet/token"
            implementation = AuthImplementation(
                self.hass,
                DOMAIN,
                ClientCredential(
                    CLIENT_ID,
                    CLIENT_SECRET,
                ),
                AuthorizationServer(
                    authorize_url=AUTHORIZE_URL,
                    token_url=url,
                ),
            )

            if not implementation:
                if self.DOMAIN in await async_get_application_credentials(self.hass):
                    return self.async_abort(reason="missing_credentials")
                return self.async_abort(reason="missing_configuration")

            req = http.current_request.get()
            if implementation and req is not None:
                # Pick first implementation if we have only one, but only
                # if this is triggered by a user interaction (request).
                self.flow_impl = implementation
                return await self.async_step_auth()

        return self.async_show_form(
            step_id="pick_implementation",
            data_schema=AUTH_SCHEMA
        )

    async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create an entry for auth."""
        # Flow has been triggered by external data
        if user_input is not None:
            self.external_data = user_input
            next_step = "authorize_rejected" if "error" in user_input else "creation"
            return self.async_external_step_done(next_step_id=next_step)

        try:
            async with asyncio.timeout(OAUTH_AUTHORIZE_URL_TIMEOUT_SEC):
                url = await self.async_generate_authorize_url()
        except TimeoutError as err:
            LOGGER.error("Timeout generating authorize url: %s", err)
            return self.async_abort(reason="authorize_url_timeout")
        except NoURLAvailableError:
            return self.async_abort(
                reason="no_url_available",
                description_placeholders={
                    "docs_url": (
                        "https://www.home-assistant.io/more-info/no-url-available"
                    )
                },
            )

        return self.async_external_step(step_id="auth", url=url)

    async def async_generate_authorize_url(self) -> str:
        """Generate a url for the user to authorize."""

        redirect_uri = get_host(self.add_url) + "/api/hanet/authcode"+ "?server_url=" + get_hc_url( self.add_url)
        return str(
            URL(self.flow_impl.authorize_url)
            .with_query(
                {
                    "response_type": "code",
                    "client_id": self.flow_impl.client_id,
                    "redirect_uri": redirect_uri,
                    "state": config_entry_oauth2_flow._encode_jwt(
                        self.hass, {"flow_id": self.flow_id, "redirect_uri": redirect_uri}
                    ),
                }
            )
            .update_query(self.flow_impl.extra_authorize_data)
        )

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return await self.async_step_pick_implementation()
    
    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow handler for this config entry."""
        return HanetOptionsFlow(config_entry)

class HanetOptionsFlow(config_entries.OptionsFlow):
    """Handle options for WebSocket Component."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        errors = {}

        # Giá trị mặc định lấy từ config_entry.data nếu options chưa có
        data = {**self.config_entry.data, **self.config_entry.options}
        self.add_url = data.get("url", HOST3)  # Lấy URL từ options hoặc mặc định HOST3
        
        if user_input is not None:
            # Nếu user nhập thông tin, validate
            selected = user_input["selected_places"]
            if not selected:
                errors["base"] = "no_place_selected"
                return self.async_show_form(
                    step_id="select_places",
                    data_schema=schema,
                    errors=errors,
                )
            
            selected_places = [
                place for place in self.places_info if str(place["place_id"]) in selected]
            
            data["selected_places"] = selected_places
            
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                options=data,                # Cập nhật options
            )
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return self.async_abort(reason="options_updated")

                # Nếu OK thì lưu options mới

        # Gọi API lấy places
        session = async_get_clientsession(self.hass)
        body_data = {
            "access_token": data["token"]["access_token"],
        }
        try:
            async with session.post(get_host(self.add_url) + API_GET_PLACES_INFO_URL, data = body_data) as response:
                if response.status == HTTPStatus.OK:
                    self.places_info = await response.json()
                else:
                    LOGGER.error("Failed to fetch places info: %s", response.status)
                    return self.async_abort(reason="fetch_places_info_failed")
        except Exception as e:
            LOGGER.error("Error fetching places info: %s", str(e))
            return self.async_abort(reason="places_info_not_found")

        places_dict = {
            str(place["place_id"]): place["place_name"] for place in self.places_info
        }
        default_selected_places = [
            str(place["place_id"]) for place in data.get("selected_places", [])
        ]
        
        # Tạo schema với default value
        schema = vol.Schema({
            vol.Required("selected_places", default=default_selected_places): cv.multi_select(places_dict)
        })


        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)