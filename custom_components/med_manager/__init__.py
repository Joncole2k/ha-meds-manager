"""HA Meds Manager integration entry point.

This file initializes:
- storage
- engine
- Home Assistant services
"""

from datetime import datetime, timezone  # Used for timestamping actions

from homeassistant.core import HomeAssistant  # Home Assistant core

from .coordinator import MedEngine  # Medication engine (scheduler loop)
from .storage import MedStorage  # Storage layer (state persistence)


# DOMAIN is the unique identifier for this integration
DOMAIN = "med_manager"


async def async_setup(hass: HomeAssistant, config: dict):
    """
    Called automatically when Home Assistant loads the integration.
    """

    # Ensure base storage exists for this integration
    hass.data.setdefault(DOMAIN, {})

    # ---------------------------------------------------------
    # Initialize storage layer
    # ---------------------------------------------------------
    storage = MedStorage(hass)

    # Store storage reference globally for later use
    hass.data[DOMAIN]["storage"] = storage

    # ---------------------------------------------------------
    # Initialize engine layer
    # ---------------------------------------------------------
    engine = MedEngine(hass)

    # Store engine reference globally for later use
    hass.data[DOMAIN]["engine"] = engine

    # Start background scheduling engine
    await engine.async_start()

    # ---------------------------------------------------------
    # REGISTER SERVICE: med_manager.take
    # ---------------------------------------------------------
    async def handle_take(call):
        """
        Service handler for marking medication as taken.

        Called from Home Assistant UI or automations.
        """

        # Extract medication ID from service call data
        med_id = call.data.get("med_id")

        # Get current timestamp in UTC
        now = datetime.now(timezone.utc).timestamp()

        # Update medication state in storage
        storage.mark_taken(med_id, now)

        # Debug log (temporary)
        print(f"[MED SERVICE] Marked taken -> {med_id} at {now}")

    # Register the service with Home Assistant
    hass.services.async_register(
        DOMAIN,
        "take",
        handle_take
    )

    # Integration successfully loaded
    return True
