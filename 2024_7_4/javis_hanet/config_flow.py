"""Config flow for Spotify."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any, Dict, cast

from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlowResult
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.const import  CONF_URL

import time
import asyncio
from http import HTTPStatus
from homeassistant.components.application_credentials import AuthImplementation
from homeassistant.components.application_credentials import ClientCredential
from homeassistant.components.application_credentials import AuthorizationServer
from homeassistant.loader import async_get_application_credentials
from homeassistant.components import http
import voluptuous as vol
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from json import JSONDecodeError
import voluptuous as vol
from homeassistant.helpers.network import NoURLAvailableError
from yarl import URL
from . import get_host, get_hc_url
from . import DOMAIN, HOST1, HOST2, HOST3, CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, SERVER_URL
OAUTH_AUTHORIZE_URL_TIMEOUT_SEC = 30


OAUTH_TOKEN_TIMEOUT_SEC = 30

LOGGER = logging.getLogger(__name__)
AUTH_SCHEMA = vol.Schema(
    {
     vol.Required(CONF_URL, default=HOST3): vol.In(
                    [HOST1, HOST2, HOST3]
                )}
)

class SpotifyFlowHandler(
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
        """Create an entry for Spotify."""
        name = data["token"]["email"]
        await self.async_set_unique_id(data["token"]["userID"])

        return self.async_create_entry(title=name, data=data)

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
        LOGGER.debug("Creating config entry from external data")
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


        # if user_input is not None:
        #     self.flow_impl = implementation
        #     return await self.async_step_auth()

        if  user_input:
            self.add_url = user_input[CONF_URL]
            url = get_host(SERVER_URL, self.add_url) + "/api/hanet/token"
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

        redirect_uri = get_host(SERVER_URL, self.add_url) + "/api/hanet/authcode"+ "?server_url=" + get_hc_url( self.add_url)
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
