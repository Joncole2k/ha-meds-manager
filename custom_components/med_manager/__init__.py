"""HA Meds Manager - Final Integration Bootstrap

This file is the MAIN ENTRY POINT for Home Assistant.

It is responsible for:

===========================================================
CORE SYSTEM BOOTSTRAP
===========================================================
- initializing storage layer
- initializing engine layer
- wiring runtime dependencies

===========================================================
SERVICE LAYER (USER ACTIONS)
===========================================================
- mark medication as taken
- snooze medication alerts
- future extensibility for skip / refill / reset

===========================================================
EVENT SYSTEM BINDING
===========================================================
- listens to engine events
- prepares automation hooks
- bridges engine → Home Assistant event bus

===========================================================
FUTURE UI / ENTITY SYSTEM SUPPORT
===========================================================
- prepares structure for sensor.med_*
- ensures compatibility with Lovelace dashboards
"""

from datetime import datetime, timezone  # timestamp handling

from homeassistant.core import HomeAssistant, ServiceCall  # Home Assistant core types

from .storage import MedStorage  # central data store

from .coordinator import MedEngine  # core scheduling engine


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

    This function wires together:
    - storage
    - engine
    - services
    - event system
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

    # Start background evaluation loop
    await engine.async_start()

    # ---------------------------------------------------------
    # SERVICE: MARK MEDICATION AS TAKEN
    # ---------------------------------------------------------

    async def handle_take(call: ServiceCall):
        """
        User marks medication as taken.

        This updates:
        - last_taken timestamp
        - resets snooze
        - triggers engine recalculation next cycle
        """

        med_id = call.data.get("med_id")

        now = datetime.now(timezone.utc).timestamp()

        storage.mark_taken(med_id, now)

        print(f"[MED SERVICE] TAKE -> {med_id}")

    # ---------------------------------------------------------
    # SERVICE: SNOOZE MEDICATION
    # ---------------------------------------------------------

    async def handle_snooze(call: ServiceCall):
        """
        User snoozes medication alerts.

        Prevents notifications until future timestamp.
        """

        med_id = call.data.get("med_id")
        minutes = call.data.get("minutes", 0)

        now = datetime.now(timezone.utc).timestamp()

        snooze_until = now + (minutes * 60)

        storage.snooze(med_id, snooze_until)

        print(f"[MED SERVICE] SNOOZE -> {med_id} ({minutes} min)")

    # ---------------------------------------------------------
    # FUTURE SERVICE HOOK: REFILL
    # ---------------------------------------------------------

    async def handle_refill(call: ServiceCall):
        """
        Placeholder for future refill tracking system.
        """

        med_id = call.data.get("med_id")

        print(f"[MED SERVICE] REFILL REQUEST -> {med_id}")

    # ---------------------------------------------------------
    # REGISTER SERVICES WITH HOME ASSISTANT
    # ---------------------------------------------------------

    hass.services.async_register(DOMAIN, "take", handle_take)
    hass.services.async_register(DOMAIN, "snooze", handle_snooze)
    hass.services.async_register(DOMAIN, "refill", handle_refill)

    # ---------------------------------------------------------
    # EVENT SYSTEM REGISTRATION (FULL PRESERVED STRUCTURE)
    # ---------------------------------------------------------

    hass.data[DOMAIN]["events"] = {
        "med_due": [],
        "med_due_soon": [],
        "med_overdue": [],
        "med_taken": [],
        "med_snoozed": []
    }

    # ---------------------------------------------------------
    # ENGINE EVENT BRIDGE
    # ---------------------------------------------------------

    def _event_listener(event):
        """
        Bridge engine events into Home Assistant event bus.

        Future:
        - automation triggers
        - UI updates
        - entity synchronization
        """

        print(f"[MED EVENT] {event.event_type} -> {event.data}")

        hass.bus.fire(event.event_type, event.data)

    # Listen to all engine events
    hass.bus.listen("med_manager_due", _event_listener)
    hass.bus.listen("med_manager_due_soon", _event_listener)
    hass.bus.listen("med_manager_overdue", _event_listener)
    hass.bus.listen("med_manager_snoozed", _event_listener)

    # ---------------------------------------------------------
    # FINAL STARTUP CONFIRMATION
    # ---------------------------------------------------------

    print("[MED MANAGER] Integration fully initialized and running")

    return True
