"""HA Meds Manager integration entry point.

This file is responsible for:
- initializing storage
- starting the engine
- registering Home Assistant services
- wiring all core components together
"""

from datetime import datetime, timezone  # Used for generating timestamps for medication actions

from homeassistant.core import HomeAssistant, ServiceCall  # Core Home Assistant types

from .storage import MedStorage  # Import medication storage layer
from .coordinator import MedEngine  # Import medication scheduling engine


# Unique identifier for this integration inside Home Assistant
DOMAIN = "med_manager"


async def async_setup(hass: HomeAssistant, config: dict):
    """
    Main setup function called automatically by Home Assistant when integration loads.
    """

    # Ensure the integration has a storage dictionary inside Home Assistant runtime
    hass.data.setdefault(DOMAIN, {})

    # ---------------------------------------------------------
    # INITIALIZE STORAGE LAYER
    # ---------------------------------------------------------

    # Create storage instance for medication data management
    storage = MedStorage(hass)

    # Store storage object inside Home Assistant shared runtime data
    hass.data[DOMAIN]["storage"] = storage

    # ---------------------------------------------------------
    # INITIALIZE ENGINE LAYER
    # ---------------------------------------------------------

    # Create medication engine instance (scheduler + evaluator)
    engine = MedEngine(hass)

    # Store engine inside Home Assistant shared runtime data
    hass.data[DOMAIN]["engine"] = engine

    # Start the background engine loop (continuous scheduling system)
    await engine.async_start()

    # ---------------------------------------------------------
    # DEFINE SERVICE: med_manager.take
    # ---------------------------------------------------------

    async def handle_take(call: ServiceCall):
        """
        Service handler for marking a medication as taken.

        This function is triggered when the user calls:
        med_manager.take
        """

        # Extract medication ID from service call payload
        med_id = call.data.get("med_id")

        # Get current UTC timestamp for logging dose time
        now = datetime.now(timezone.utc).timestamp()

        # Retrieve medication record from storage
        med = storage.get_med(med_id)

        # If medication does not exist, log and safely exit
        if not med:
            print(f"[MED SERVICE] Medication not found: {med_id}")
            return

        # Update medication with new last_taken timestamp
        med["last_taken"] = now

        # Save updated medication back into storage layer
        storage.update_med(med_id, med)

        # Debug output for verification during development
        print(f"[MED SERVICE] Marked taken: {med_id} @ {now}")

    # ---------------------------------------------------------
    # REGISTER SERVICE WITH HOME ASSISTANT
    # ---------------------------------------------------------

    hass.services.async_register(
        DOMAIN,  # service domain (med_manager)
        "take",   # service name (med_manager.take)
        handle_take  # function executed when service is called
    )

    # Log successful integration startup
    print("[MED MANAGER] Integration started successfully")

    # Return True tells Home Assistant setup completed successfully
    return True
