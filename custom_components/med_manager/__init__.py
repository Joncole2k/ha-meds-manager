"""HA Meds Manager Integration Entry Point.

This file is the MAIN ENTRY POINT for Home Assistant.

It is responsible for:
- initializing storage layer
- initializing engine layer
- registering Home Assistant services
- preparing future entity + automation hooks
"""

from datetime import datetime, timezone  # Used for timestamps

from homeassistant.core import HomeAssistant, ServiceCall  # Core HA types

from .storage import MedStorage  # Medication storage system

from .coordinator import MedEngine  # Core scheduling engine


# ---------------------------------------------------------
# DOMAIN IDENTIFIER
# ---------------------------------------------------------
DOMAIN = "med_manager"


# ---------------------------------------------------------
# INTEGRATION SETUP ENTRYPOINT
# ---------------------------------------------------------
async def async_setup(hass: HomeAssistant, config: dict):
    """
    Called automatically when Home Assistant loads the integration.
    """

    # ---------------------------------------------------------
    # CORE NAMESPACE INITIALIZATION
    # ---------------------------------------------------------

    hass.data.setdefault(DOMAIN, {})

    # ---------------------------------------------------------
    # STORAGE INITIALIZATION
    # ---------------------------------------------------------

    storage = MedStorage(hass)
    hass.data[DOMAIN]["storage"] = storage

    # ---------------------------------------------------------
    # ENGINE INITIALIZATION
    # ---------------------------------------------------------

    engine = MedEngine(hass)
    hass.data[DOMAIN]["engine"] = engine

    # Start background engine loop
    await engine.async_start()

    # ---------------------------------------------------------
    # SERVICE: MARK MEDICATION AS TAKEN
    # ---------------------------------------------------------

    async def handle_take(call: ServiceCall):
        """
        User marks medication as taken.
        """

        med_id = call.data.get("med_id")

        now = datetime.now(timezone.utc).timestamp()

        storage.mark_taken(med_id, now)

        print(f"[MED SERVICE] Taken -> {med_id}")

    # ---------------------------------------------------------
    # SERVICE: SNOOZE MEDICATION ALERTS
    # ---------------------------------------------------------

    async def handle_snooze(call: ServiceCall):
        """
        User snoozes medication notifications.
        """

        med_id = call.data.get("med_id")
        minutes = call.data.get("minutes", 0)

        now = datetime.now(timezone.utc).timestamp()

        snooze_until = now + (minutes * 60)

        storage.snooze(med_id, snooze_until)

        print(f"[MED SERVICE] Snoozed -> {med_id} for {minutes} min")

    # ---------------------------------------------------------
    # REGISTER SERVICES WITH HOME ASSISTANT
    # ---------------------------------------------------------

    hass.services.async_register(
        DOMAIN,
        "take",
        handle_take
    )

    hass.services.async_register(
        DOMAIN,
        "snooze",
        handle_snooze
    )

    # ---------------------------------------------------------
    # FUTURE HOOKS (PLACEHOLDER FOR ENTITIES + EVENTS)
    # ---------------------------------------------------------

    hass.data[DOMAIN]["events"] = {
        "med_due": [],
        "med_taken": [],
        "med_overdue": []
    }

    print("[MED MANAGER] Integration fully initialized")

    return True
