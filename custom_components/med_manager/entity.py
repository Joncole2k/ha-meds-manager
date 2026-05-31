"""
HA Meds Manager - Entity Layer (FINAL MODERN VERSION)

===========================================================
PURPOSE
===========================================================
This file exposes medications as Home Assistant entities.

Each medication becomes:
- sensor.med_<id>

Entities reflect:
- status (due / due_soon / overdue / not_due / snoozed)
- full metadata via attributes

===========================================================
MODERN HA ARCHITECTURE (2026 READY)
===========================================================
- async_setup_entry (NOT legacy platform setup)
- dispatcher-based updates (real-time UI sync)
- storage-driven entity refresh
- safe update model (no stale references)

===========================================================
UI COMPATIBILITY
===========================================================
Works with:
- Lovelace default cards
- Mushroom cards
- Custom mod-card dashboards
"""

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .storage import MedStorage


# ---------------------------------------------------------
# DOMAIN IDENTIFIER
# ---------------------------------------------------------
DOMAIN = "med_manager"

# Signal used to notify all entities to refresh
SIGNAL_UPDATE = "med_manager_update"


# ---------------------------------------------------------
# SETUP ENTRY (MODERN HA WAY)
# ---------------------------------------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    """
    Creates medication entities dynamically from storage.
    """

    storage = MedStorage(hass)

    meds = storage.get_all()

    entities = []

    for med_id, med in meds.items():
        entities.append(MedSensor(hass, storage, med_id))

    async_add_entities(entities)

    # ---------------------------------------------------------
    # GLOBAL UPDATE SIGNAL
    # ---------------------------------------------------------
    def _handle_update():
        """Force all entities to refresh from storage."""

        for entity in entities:
            entity.async_schedule_update_ha_state(True)

    async_dispatcher_connect(hass, SIGNAL_UPDATE, _handle_update)


# ---------------------------------------------------------
# MEDICATION SENSOR ENTITY
# ---------------------------------------------------------
class MedSensor(SensorEntity):
    """
    Single medication entity.
    """

    def __init__(self, hass, storage, med_id):
        self.hass = hass
        self.storage = storage
        self._med_id = med_id
        self._data = {}

    # ---------------------------------------------------------
    # IDENTITY
    # ---------------------------------------------------------
    @property
    def name(self):
        return f"med_{self._med_id}"

    @property
    def unique_id(self):
        return f"med_manager_{self._med_id}"

    # ---------------------------------------------------------
    # STATE
    # ---------------------------------------------------------
    @property
    def state(self):
        self._refresh()
        return self._data.get("status", "unknown")

    # ---------------------------------------------------------
    # ATTRIBUTES (FULL DASHBOARD SUPPORT)
    # ---------------------------------------------------------
    @property
    def extra_state_attributes(self):
        self._refresh()

        return {
            "name": self._data.get("name"),
            "generic_name": self._data.get("generic_name"),
            "brand": self._data.get("brand"),
            "person": self._data.get("person"),

            "interval_hours": self._data.get("interval_hours"),
            "last_taken": self._data.get("last_taken"),
            "next_due": self._data.get("next_due"),

            "snooze_until": self._data.get("snooze_until"),

            "status": self._data.get("status"),

            "current_count": self._data.get("current_count"),
            "low_stock_threshold": self._data.get("low_stock_threshold"),

            "refill_required": self._data.get("refill_required"),
        }

    # ---------------------------------------------------------
    # UPDATE SYSTEM
    # ---------------------------------------------------------
    def _refresh(self):
        """Pull latest data from storage (always fresh)."""

        med = self.storage.get_med(self._med_id)

        if med:
            self._data = med

    # ---------------------------------------------------------
    # HA UPDATE TRIGGER
    # ---------------------------------------------------------
    async def async_update(self):
        """Called by Home Assistant refresh cycle."""

        self._refresh()
