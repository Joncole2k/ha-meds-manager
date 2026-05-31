"""HA Meds Manager Storage Layer.

This file manages all medication data storage.

Current design:
- Uses hass.data for runtime persistence
- Automatically seeds demo data if storage is empty (for testing)
- Will later migrate to Home Assistant Store API for persistence
"""

from datetime import datetime, timezone  # Used for generating demo timestamps

from homeassistant.core import HomeAssistant  # Home Assistant core access


# DOMAIN key used inside hass.data
DOMAIN = "med_manager"


class MedStorage:
    """
    Storage layer for medication data.

    Responsible for:
    - storing medication records
    - retrieving medication records
    - updating medication records
    - providing initial demo data for testing
    """

    def __init__(self, hass: HomeAssistant):
        # Store Home Assistant reference
        self.hass = hass

        # Ensure integration storage exists in hass.data
        self.hass.data.setdefault(DOMAIN, {})

        # Ensure medication container exists
        self.hass.data[DOMAIN].setdefault("medications", {})

        # ---------------------------------------------------------
        # AUTO-SEED DEMO DATA (ONLY IF EMPTY)
        # ---------------------------------------------------------
        if not self.hass.data[DOMAIN]["medications"]:
            self._seed_demo_data()

    def get_all(self):
        """
        Return all medication records.
        """
        return self.hass.data[DOMAIN]["medications"]

    def set_all(self, data):
        """
        Replace all medication records.
        """
        self.hass.data[DOMAIN]["medications"] = data

    def get_med(self, med_id):
        """
        Retrieve a single medication by ID.
        """
        return self.hass.data[DOMAIN]["medications"].get(med_id)

    def update_med(self, med_id, med_data):
        """
        Update or create medication entry.
        """
        self.hass.data[DOMAIN]["medications"][med_id] = med_data

    def mark_taken(self, med_id, timestamp):
        """
        Mark a medication as taken.

        This updates:
        - last_taken timestamp
        """

        # Retrieve medication entry
        med = self.get_med(med_id)

        # If medication does not exist, exit safely
        if not med:
            print(f"[MED STORAGE] Medication not found: {med_id}")
            return

        # Update last_taken time
        med["last_taken"] = timestamp

        # Save updated record
        self.update_med(med_id, med)

    def _seed_demo_data(self):
        """
        Create initial demo medication data.

        This allows the system to run immediately after install
        without requiring user configuration.
        """

        # Current UTC time for baseline calculations
        now = datetime.now(timezone.utc).timestamp()

        # Create sample medication entry
        self.hass.data[DOMAIN]["medications"] = {
            "jonathan_001": {
                "name": "Demo Medication",
                "last_taken": now - 7200,  # taken 2 hours ago
                "interval_hours": 6
            }
        }

        print("[MED STORAGE] Demo medication data initialized.")
