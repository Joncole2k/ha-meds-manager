"""HA Meds Manager Storage Layer.

This file defines the COMPLETE medication data model and storage system.

It is responsible for:
- storing medication definitions
- storing scheduling state
- storing snooze state
- storing notification state
- supporting future entity + UI mapping

This is the SINGLE SOURCE OF TRUTH for all medication data.
"""

from datetime import datetime, timezone  # Used for timestamps and scheduling

from homeassistant.core import HomeAssistant  # Home Assistant system access


# ---------------------------------------------------------
# DOMAIN KEY
# ---------------------------------------------------------
DOMAIN = "med_manager"


class MedStorage:
    """
    Central medication storage system.

    This class is responsible for ALL state persistence including:
    - medication definitions
    - scheduling state
    - user actions (taken, snoozed, skipped)
    - notification tracking
    """

    def __init__(self, hass: HomeAssistant):
        # Store Home Assistant reference
        self.hass = hass

        # Ensure integration namespace exists
        self.hass.data.setdefault(DOMAIN, {})

        # Ensure medication container exists
        self.hass.data[DOMAIN].setdefault("medications", {})

        # Initialize demo data if empty (safe bootstrap for testing)
        if not self.hass.data[DOMAIN]["medications"]:
            self._seed_demo_data()

    # ---------------------------------------------------------
    # CORE ACCESS METHODS
    # ---------------------------------------------------------

    def get_all(self):
        """Return all medication records."""
        return self.hass.data[DOMAIN]["medications"]

    def get_med(self, med_id):
        """Return single medication by ID."""
        return self.hass.data[DOMAIN]["medications"].get(med_id)

    def update_med(self, med_id, med_data):
        """Update or create medication record."""
        self.hass.data[DOMAIN]["medications"][med_id] = med_data

    # ---------------------------------------------------------
    # ACTION METHODS (USER INTERACTIONS)
    # ---------------------------------------------------------

    def mark_taken(self, med_id, timestamp):
        """
        User action: medication taken.

        Updates:
        - last_taken
        - clears snooze (if active)
        """

        med = self.get_med(med_id)

        if not med:
            return

        med["last_taken"] = timestamp
        med["snooze_until"] = None  # clear snooze when taken

        self.update_med(med_id, med)

    def snooze(self, med_id, until_timestamp):
        """
        User action: snooze medication alerts until time.
        """

        med = self.get_med(med_id)

        if not med:
            return

        med["snooze_until"] = until_timestamp

        self.update_med(med_id, med)

    def mark_notified(self, med_id, timestamp):
        """
        Track last notification time to prevent spam.
        """

        med = self.get_med(med_id)

        if not med:
            return

        med["last_notified"] = timestamp

        self.update_med(med_id, med)

    # ---------------------------------------------------------
    # DEMO DATA (FULL STRUCTURE MODEL)
    # ---------------------------------------------------------

    def _seed_demo_data(self):
        """
        Create full example medication structure.

        This defines the STANDARD DATA MODEL used everywhere.
        """

        now = datetime.now(timezone.utc).timestamp()

        self.hass.data[DOMAIN]["medications"] = {
            "med_jonathan_001": {
                # -------------------------------------------------
                # IDENTITY
                # -------------------------------------------------
                "name": "Tylenol",
                "person": "jonathan",

                # -------------------------------------------------
                # SCHEDULING MODEL
                # -------------------------------------------------
                "interval_hours": 6,
                "last_taken": now - 7200,  # 2 hours ago
                "next_due": None,  # engine will compute

                # -------------------------------------------------
                # STATE TRACKING
                # -------------------------------------------------
                "status": "unknown",

                # -------------------------------------------------
                # USER CONTROL STATES
                # -------------------------------------------------
                "snooze_until": None,

                # -------------------------------------------------
                # NOTIFICATION TRACKING
                # -------------------------------------------------
                "last_notified": None,
                "notification_count": 0,

                # -------------------------------------------------
                # INVENTORY (future-ready)
                # -------------------------------------------------
                "current_count": 30,
                "low_stock_threshold": 5,

                # -------------------------------------------------
                # FUTURE UI / ENTITY MAPPING
                # -------------------------------------------------
                "entity_id": "sensor.med_jonathan_tylenol"
            }
        }
