"""HA Meds Manager integration entry point.

This file is loaded by Home Assistant when the integration starts.
"""

from homeassistant.core import HomeAssistant  # Home Assistant core type hints

# DOMAIN is the unique identifier for this integration inside Home Assistant
DOMAIN = "med_manager"


async def async_setup(hass: HomeAssistant, config: dict):
    """
    Called automatically by Home Assistant when the integration is loaded.

    hass: Home Assistant instance (global system access)
    config: YAML configuration (we are NOT using this yet)
    """

    # Create a storage area for our integration inside Home Assistant
    # This is where we will later store engine + runtime state
    hass.data.setdefault(DOMAIN, {})

    # Return True tells Home Assistant:
    # "Integration loaded successfully"
    return True
