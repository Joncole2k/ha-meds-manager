"""
HA Meds Manager - Entity Layer (FINAL)

This file exposes medications as Home Assistant sensor entities.

===========================================================
PURPOSE
===========================================================
Transforms stored medication data into:
- sensor.med_* entities
- UI-visible attributes
- real-time state updates

===========================================================
ARCHITECTURE MODEL
===========================================================
Storage (source of truth)
        ↓
Engine (updates state)
        ↓
Entity layer (displays state in Home Assistant UI)

===========================================================
EVENT MODEL
===========================================================
Entities update via:
- HA polling update() fallback
- Event-driven refresh from engine signals

===========================================================
UI COMPATIBILITY
===========================================================
Designed for:
- Lovelace dashboards
- Mushroom cards
- custom UI cards
"""

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant

from .storage import MedStorage

import asyncio


# ---------------------------------------------------------
# DOMAIN IDENTIFIER
# ---------------------------------------------------------
DOMAIN = "med_manager"


# ---------------------------------------------------------
# ENTITY SETUP
# ---------------------------------------------------------
async def async_setup_platform(
    hass: HomeAssistant,
    config,
    async_add_entities,
    discovery_info=None
):
    """
    Create sensor entities for all medications in storage.
    """

    storage = MedStorage(hass)
    meds = storage.get_all()

    entities = []

    for med_id, med in meds.items():
        entities.append(MedSensor(hass, med_id))

    async_add_entities(entities, True)


# ---------------------------------------------------------
# MEDICATION SENSOR ENTITY
# ---------------------------------------------------------
class MedSensor(SensorEntity):
    """
    Represents a single medication as a Home Assistant sensor.
    """

    def __init__(self, hass, med_id):
        self.hass = hass
        self._med_id = med_id
        self._storage = MedStorage(hass)
        self._data = None

        # Subscribe to HA event bus for reactive updates
        self.hass.bus.listen("med_manager_due", self._handle_event)
        self.hass.bus.listen("med_manager_due_soon", self._handle_event)
        self.hass.bus.listen("med_manager_overdue", self._handle_event)
        self.hass.bus.listen("med_manager_snoozed", self._handle_event)

    # ---------------------------------------------------------
    # IDENTITY
    # ---------------------------------------------------------
    @property
    def name(self):
        med = self._get_data()
        return f"med_{med.get('common_name', self._med_id)}"

    @property
    def unique_id(self):
        return self._med_id

    # ---------------------------------------------------------
    # STATE
    # ---------------------------------------------------------
    @property
    def state(self):
        med = self._get_data()
        return med.get("status", "unknown")

    # ---------------------------------------------------------
    # ATTRIBUTES (FULL UI EXPOSURE)
    # ---------------------------------------------------------
    @property
    def extra_state_attributes(self):
        med = self._get_data()

        return {
            # Identity
            "common_name": med.get("common_name"),
            "generic_name": med.get("generic_name"),
            "brand_name": med.get("brand_name"),
            "person": med.get("person"),

            # Scheduling
            "interval_hours": med.get("interval_hours"),
            "last_taken": med.get("last_taken"),
            "next_due": med.get("next_due"),

            # User state
            "snooze_until": med.get("snooze_until"),

            # Notifications
            "last_notified": med.get("last_notified"),

            # Inventory
            "current_count": med.get("current_count"),
            "low_stock_threshold": med.get("low_stock_threshold"),
            "refill_required": med.get("refill_required"),

            # UI metadata
            "entity_id": self._med_id,
        }

    # ---------------------------------------------------------
    # DATA ACCESS LAYER
    # ---------------------------------------------------------
    def _get_data(self):
        self._data = self._storage.get_med(self._med_id) or {}
        return self._data

    # ---------------------------------------------------------
    # REFRESH (HA POLLING FALLBACK)
    # ---------------------------------------------------------
    def update(self):
        self._get_data()

    # ---------------------------------------------------------
    # EVENT-DRIVEN REFRESH
    # ---------------------------------------------------------
    def _handle_event(self, event):
        """
        Called when engine emits state changes.
        Forces UI refresh.
        """

        if hasattr(self, "async_write_ha_state"):
            self.async_write_ha_state()
