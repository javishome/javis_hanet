"""Config flow for Spotify."""

from __future__ import annotations

import logging
from typing import Any, Dict, cast

from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.const import  CONF_URL
from homeassistant.data_entry_flow import FlowResult
import async_timeout
import time
import asyncio
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
from . import HOST1, HOST2, HOST3, CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, DOMAIN

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

    async def async_oauth_create_entry(self, data: dict[str, Any]):
        """Create an entry for Spotify."""
        name = data["token"]["email"]
        await self.async_set_unique_id(data["token"]["userID"])

        return self.async_create_entry(title=name, data=data)

    async def async_step_creation(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Create config entry from external data."""
        data = {
            "grant_type": "authorization_code",
            "code": self.external_data["code"],
            "redirect_uri": self.external_data["state"]["redirect_uri"],
        }
        session = async_get_clientsession(self.hass)
        resp = await session.post(self.flow_impl.token_url, data=data)
        if resp.status >= 400 and LOGGER.isEnabledFor(logging.DEBUG):
            body = await resp.text()
            LOGGER.debug(
                "Token request failed with status=%s, body=%s",
                resp.status,
                body,
            )
        resp.raise_for_status()
        token = cast(dict, await resp.json())
        # Force int for non-compliant oauth2 providers
        try:
            token["expires_in"] = int(token["expire"])
        except ValueError as err:
            LOGGER.warning("Error converting expires_in to int: %s", err)
            return self.async_abort(reason="oauth_error")
        token["expires_at"] = time.time() + token["expires_in"]

        self.logger.info("Successfully authenticated")

        return await self.async_oauth_create_entry(
            {"auth_implementation": self.flow_impl.domain, "token": token, "url": self.add_url}
        )

    async def async_step_pick_implementation(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle a flow start."""

        if user_input :
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
    ) -> FlowResult:
        """Create an entry for auth."""
        # Flow has been triggered by external data
        if user_input is not None:
            self.external_data = user_input
            next_step = "authorize_rejected" if "error" in user_input else "creation"
            return self.async_external_step_done(next_step_id=next_step)

        try:
            async with async_timeout.timeout(10):
                url = await self.async_generate_authorize_url()
        except asyncio.TimeoutError:
            return self.async_abort(reason="authorize_url_timeout")
        except NoURLAvailableError:
            return self.async_abort(
                reason="no_url_available",
                description_placeholders={
                    "docs_url": "https://www.home-assistant.io/more-info/no-url-available"
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
