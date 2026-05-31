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
- async_setup_entry (modern config entry flow)
- dispatcher-based updates (real-time UI sync)
- storage-driven entity refresh
- safe update model (no stale references)

===========================================================
UI COMPATIBILITY
===========================================================
Works with:
- Lovelace default cards
- Mushroom cards
- custom mod-card dashboards
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

# ---------------------------------------------------------
# GLOBAL UPDATE SIGNAL
# ---------------------------------------------------------
SIGNAL_UPDATE = "med_manager_update"


# =========================================================
# SETUP ENTRY (ONLY VALID ENTRY POINT)
# =========================================================
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    """
    Creates medication entities dynamically from storage.
    """

    # ---------------------------------------------------------
    # STORAGE ACCESS (SINGLE SOURCE OF TRUTH)
    # ---------------------------------------------------------
    storage = hass.data[DOMAIN]["storage"]
    meds = storage.get_all()

    # ---------------------------------------------------------
    # ENTITY LIST
    # ---------------------------------------------------------
    entities = []

    for med_id in meds:
        entities.append(MedSensor(hass, storage, med_id))

    # ---------------------------------------------------------
    # INITIAL ADD (IMPORTANT)
    # ---------------------------------------------------------
    async_add_entities(entities, update_before_add=True)

    # ---------------------------------------------------------
    # DISPATCHER UPDATE HOOK
    # ---------------------------------------------------------
    def _handle_update():
        """Force all entities to refresh state."""
        for entity in entities:
            entity._refresh()
            entity.async_write_ha_state()

    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            SIGNAL_UPDATE,
            lambda _: _handle_update()
        )
    )


# =========================================================
# MEDICATION SENSOR ENTITY
# =========================================================
class MedSensor(SensorEntity):

    def __init__(self, hass, storage, med_id):
        self.hass = hass
        self.storage = storage
        self._med_id = med_id
        self._data = {}

        # -----------------------------------------------------
        # INITIAL LOAD (CRITICAL FIX)
        # -----------------------------------------------------
        self._refresh()

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
        return self._data.get("status", "unknown")

    # ---------------------------------------------------------
    # ATTRIBUTES
    # ---------------------------------------------------------
    @property
    def extra_state_attributes(self):
        return self._data

    # ---------------------------------------------------------
    # REFRESH
    # ---------------------------------------------------------
    def _refresh(self):
        med = self.storage.get_med(self._med_id)
        if med:
            self._data = med

    # ---------------------------------------------------------
    # UPDATE CYCLE
    # ---------------------------------------------------------
    async def async_update(self):
        self._refresh()

    # ---------------------------------------------------------
    # REALTIME UPDATES
    # ---------------------------------------------------------
    async def async_added_to_hass(self):

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_UPDATE,
                self._handle_dispatch_update
            )
        )

    async def _handle_dispatch_update(self, *_):
        self._refresh()
        self.async_write_ha_state()
