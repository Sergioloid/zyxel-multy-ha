"""Config flow for Zyxel Multy integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from .api import ZapiAuthError, ZapiError, ZyxelMultyApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="192.168.212.1"): str,
        vol.Required(CONF_USERNAME, default="admin"): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class ZyxelMultyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zyxel Multy."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api = ZyxelMultyApi(
                host=user_input[CONF_HOST],
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
            )

            try:
                await api.authenticate()
                info = await api.get_system_info()
                model_name = "Zyxel Multy"
                if isinstance(info, dict):
                    model_name = info.get("model-name", "Zyxel Multy")
            except ZapiAuthError:
                errors["base"] = "invalid_auth"
            except ZapiError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self._async_abort_if_unique_id_configured()
                await api.close()

                return self.async_create_entry(
                    title=f"{model_name} ({user_input[CONF_HOST]})",
                    data=user_input,
                )
            finally:
                await api.close()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
