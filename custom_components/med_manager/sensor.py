"""HA Meds Manager - Entity Layer (FINAL)

This file exposes medications as Home Assistant entities.

===========================================================
PURPOSE
===========================================================
Transforms stored medication data into:
- sensor.med_* entities
- UI-visible attributes
- real-time state updates

===========================================================
UI OUTPUT
===========================================================
Each medication becomes a sensor with:
- state = medication status
- attributes = full medication metadata

===========================================================
ACTION MODEL
===========================================================
Actions are NOT handled here directly.
They are routed through:
- services in __init__.py
- engine in coordinator.py
"""

from homeassistant.components.sensor import SensorEntity  # HA sensor base class
from homeassistant.core import HomeAssistant  # HA system reference
from homeassistant.helpers.entity_platform import AddEntitiesCallback  # NEW (required)
from homeassistant.config_entries import ConfigEntry  # NEW (required)

from .storage import MedStorage  # shared data layer


# ---------------------------------------------------------
# DOMAIN IDENTIFIER
# ---------------------------------------------------------
DOMAIN = "med_manager"


# ---------------------------------------------------------
# ENTITY PLATFORM SETUP
# ---------------------------------------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    """
    Creates sensor entities for all medications.

    This runs once and builds entity list from storage.
    """

    # ---------------------------------------------------------
    # STORAGE INITIALIZATION
    # ---------------------------------------------------------
    storage = MedStorage(hass)

    # ---------------------------------------------------------
    # LOAD ALL MEDICATIONS
    # ---------------------------------------------------------
    meds = storage.get_all()

    # ---------------------------------------------------------
    # ENTITY LIST BUILD
    # ---------------------------------------------------------
    entities = []

    for med_id, med in meds.items():
        entities.append(MedSensor(hass, med_id, med))
        
    # ---------------------------------------------------------
    # REGISTER ENTITIES
    # ---------------------------------------------------------
    async_add_entities(entities, True)

# ---------------------------------------------------------
# MEDICATION SENSOR ENTITY
# ---------------------------------------------------------
class MedSensor(SensorEntity):
    """
    Represents a single medication as a Home Assistant sensor.

    State:
        - due
        - due_soon
        - overdue
        - not_due
        - snoozed

    Attributes:
        - full medication metadata
        - scheduling data
        - inventory data
    """

    def __init__(self, hass, med_id, data):
        # ---------------------------------------------------------
        # CORE REFERENCES
        # ---------------------------------------------------------
        self.hass = hass
        self._med_id = med_id
        self._data = data

    # ---------------------------------------------------------
    # ENTITY IDENTITY
    # ---------------------------------------------------------

    @property
    def name(self):
        return f"med_{self._med_id}"

    @property
    def unique_id(self):
        return f"med_manager_{self._med_id}"
        
    # ---------------------------------------------------------
    # STATE VALUE
    # ---------------------------------------------------------

    @property
    def state(self):
        return self._data.get("status", "unknown")

    # ---------------------------------------------------------
    # ATTRIBUTES (FULL DATA EXPOSURE)
    # ---------------------------------------------------------

    @property
    def extra_state_attributes(self):
        return {
            # -------------------------------------------------
            # IDENTITY
            # -------------------------------------------------
            "common_name": self._data.get("common_name"),
            "generic_name": self._data.get("generic_name"),
            "brand_name": self._data.get("brand_name"),
            "person": self._data.get("person"),

            # -------------------------------------------------
            # SCHEDULING
            # -------------------------------------------------
            "interval_hours": self._data.get("interval_hours"),
            "last_taken": self._data.get("last_taken"),
            "next_due": self._data.get("next_due"),

            # -------------------------------------------------
            # USER STATE
            # -------------------------------------------------
            "snooze_until": self._data.get("snooze_until"),

            # -------------------------------------------------
            # NOTIFICATIONS
            # -------------------------------------------------
            "last_notified": self._data.get("last_notified"),

            # -------------------------------------------------
            # INVENTORY
            # -------------------------------------------------
            "current_count": self._data.get("current_count"),
            "low_stock_threshold": self._data.get("low_stock_threshold"),
            "refill_required": self._data.get("refill_required"),

            # -------------------------------------------------
            # UI / ENGINE DEBUG
            # -------------------------------------------------
            "entity_id": self._med_id,
        }

    # ---------------------------------------------------------
    # AUTO REFRESH SUPPORT
    # ---------------------------------------------------------

    def update(self):
        """
        Pull latest state from storage every refresh cycle.
        """

        # ---------------------------------------------------------
        # STORAGE ACCESS
        # ---------------------------------------------------------
        storage = MedStorage(self.hass)

        # ---------------------------------------------------------
        # REFRESH LOCAL STATE
        # ---------------------------------------------------------
        self._data = storage.get_med(self._med_id)
