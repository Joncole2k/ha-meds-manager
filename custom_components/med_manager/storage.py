"""
HA Meds Manager - Storage Layer (FINAL PRODUCT MODEL)

This file defines the COMPLETE medication data structure used across:
- Engine (scheduling + evaluation)
- Services (take / snooze / refill / create / delete)
- Notifications
- Future entities (sensor.med_*)
- Future UI dashboards (Lovelace cards)

This is the SINGLE SOURCE OF TRUTH for all medication state.
"""

from datetime import datetime, timezone  # Timestamp handling

from homeassistant.core import HomeAssistant  # Home Assistant access


# ---------------------------------------------------------
# DOMAIN IDENTIFIER
# ---------------------------------------------------------
DOMAIN = "med_manager"


class MedStorage:
    """
    Central medication storage system.

    This class handles:
    - persistence (runtime via hass.data)
    - full medication schema storage
    - state tracking for engine + UI + entities
    """

    def __init__(self, hass: HomeAssistant):
        # Store Home Assistant instance
        self.hass = hass

        # Initialize integration namespace (safe re-entry)
        self.hass.data.setdefault(DOMAIN, {})

        # Initialize medication store (single source of truth)
        self.hass.data[DOMAIN].setdefault("medications", {})

        # Ensure demo data exists for immediate testing
        if not self.hass.data[DOMAIN]["medications"]:
            self._seed_demo_data()

    # ---------------------------------------------------------
    # CORE ACCESS METHODS
    # ---------------------------------------------------------

    def get_all(self):
        """Return all medication records."""
        return self.hass.data[DOMAIN]["medications"]

    def get_med(self, med_id):
        """Get single medication record."""
        return self.hass.data[DOMAIN]["medications"].get(med_id)

    def update_med(self, med_id, data):
        """Update full medication record."""
        self.hass.data[DOMAIN]["medications"][med_id] = data

    # ---------------------------------------------------------
    # USER ACTION METHODS (SERVICES)
    # ---------------------------------------------------------

    def mark_taken(self, med_id, timestamp):
        """User action: medication taken."""
        med = self.get_med(med_id)
        if not med:
            return

        med["last_taken"] = timestamp
        med["snooze_until"] = None

        self.update_med(med_id, med)

    def snooze(self, med_id, until_timestamp):
        """User action: snooze medication alerts."""
        med = self.get_med(med_id)
        if not med:
            return

        med["snooze_until"] = until_timestamp
        self.update_med(med_id, med)

    def mark_notified(self, med_id, timestamp):
        """Engine action: tracks notifications to prevent spam."""
        med = self.get_med(med_id)
        if not med:
            return

        med["last_notified"] = timestamp
        med["notification_count"] = med.get("notification_count", 0) + 1

        self.update_med(med_id, med)

    # ---------------------------------------------------------
    # INVENTORY / REFILL SYSTEM
    # ---------------------------------------------------------

    def refill(self, med_id, amount):
        """Update medication inventory after refill."""
        med = self.get_med(med_id)
        if not med:
            return

        med["current_count"] = amount
        med["refill_required"] = False

        self.update_med(med_id, med)

    # ---------------------------------------------------------
    # CREATE / DELETE MEDICATION
    # ---------------------------------------------------------

    def create_medication(self, med_id, data):
        """Create a new medication entry."""
        self.hass.data[DOMAIN]["medications"][med_id] = data

    def delete_medication(self, med_id):
        """Delete medication entry."""
        if med_id in self.hass.data[DOMAIN]["medications"]:
            del self.hass.data[DOMAIN]["medications"][med_id]

    # ---------------------------------------------------------
    # DEMO DATA (FULL SYSTEM SCHEMA)
    # ---------------------------------------------------------

    def _seed_demo_data(self):
        """Creates full schema example medication."""

        now = datetime.now(timezone.utc).timestamp()

        self.hass.data[DOMAIN]["medications"] = {
            "med_jonathan_tylenol": {
                # -------------------------------------------------
                # IDENTITY LAYER
                # -------------------------------------------------
                "common_name": "Tylenol",
                "generic_name": "acetaminophen",
                "brand_name": "Equate",
                "person": "jonathan",

                # -------------------------------------------------
                # SCHEDULING MODEL
                # -------------------------------------------------
                "interval_hours": 6,
                "last_taken": now - 7200,
                "next_due": None,

                # -------------------------------------------------
                # ENGINE STATE
                # -------------------------------------------------
                "status": "unknown",

                # -------------------------------------------------
                # SNOOZE SYSTEM
                # -------------------------------------------------
                "snooze_until": None,

                # -------------------------------------------------
                # NOTIFICATION SYSTEM
                # -------------------------------------------------
                "last_notified": None,
                "notification_count": 0,

                # -------------------------------------------------
                # INVENTORY MANAGEMENT
                # -------------------------------------------------
                "current_count": 30,
                "original_count": 30,
                "low_stock_threshold": 5,
                "refill_required": False,
                "refill_type": "non_refillable",

                # -------------------------------------------------
                # UI / ENTITY LAYER
                # -------------------------------------------------
                "entity_id": "sensor.med_jonathan_tylenol",
                "ui_group": "jonathan_medications",

                # -------------------------------------------------
                # AUTOMATION HOOKS
                # -------------------------------------------------
                "event_enabled": True
            }
        }
