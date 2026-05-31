"""HA Meds Manager integration entry point.

This file is loaded by Home Assistant when the integration starts.
It is responsible for initializing and starting the medication engine.
"""

from homeassistant.core import HomeAssistant  # Home Assistant core type hints

from .coordinator import MedEngine  # Import the medication engine (core scheduler loop)


# DOMAIN is the unique identifier for this integration inside Home Assistant
# It is used as the key in hass.data storage
DOMAIN = "med_manager"


async def async_setup(hass: HomeAssistant, config: dict):
    """
    Called automatically by Home Assistant when the integration is loaded.

    This function is the entry point for setting up the integration.
    """

    # Ensure a storage container exists for this integration inside Home Assistant
    # hass.data is shared runtime memory used by integrations
    hass.data.setdefault(DOMAIN, {})

    # Create an instance of the medication engine
    # This engine will handle all scheduling logic and state evaluation
    engine = MedEngine(hass)

    # Store the engine inside Home Assistant's runtime data registry
    # This allows other parts of the integration to access it later
    hass.data[DOMAIN]["engine"] = engine

    # Start the background engine loop
    # This begins continuous medication scheduling evaluation
    await engine.async_start()

    # Return True signals to Home Assistant:
    # "Integration loaded and started successfully"
    return True
