"""Application credentials platform for spotify."""

from homeassistant.components.application_credentials import AuthorizationServer
from homeassistant.core import HomeAssistant
from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
)
from .const import DOMAIN
from homeassistant.helpers.typing import ConfigType



async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer:
    """Return authorization server."""

    client_id = "94414a66f3c6a7e2ceadc17af8ccdd60"
    client_secret = "9b1c225a0c3df7660b5ba8a025ebbefc"
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(
            client_id,
            client_secret,
        ),
    )

    return AuthorizationServer(
        authorize_url="https://oauth.hanet.com/oauth2/authorize",
        token_url="https://oauth.hanet.com/token",
    )

# async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
#     """Set up the component."""


