"""HA Meds Manager Storage Layer.

This file handles how medication data is stored and retrieved.

We use hass.data for runtime persistence (in-memory during runtime).
Later this will be upgraded to persistent Home Assistant storage.
"""

from homeassistant.core import HomeAssistant  # Core Home Assistant access


# DOMAIN is the key used inside hass.data to store integration data
DOMAIN = "med_manager"


class MedStorage:
    """
    Storage wrapper for medication data.

    This class is responsible for:
    - retrieving medication data
    - updating medication data
    - managing medication state changes
    """

    def __init__(self, hass: HomeAssistant):
        # Reference to Home Assistant instance
        self.hass = hass

        # Ensure integration storage exists
        self.hass.data.setdefault(DOMAIN, {})

        # Ensure medication container exists
        self.hass.data[DOMAIN].setdefault("medications", {})

    def get_all(self):
        """
        Return all medication records.
        """
        return self.hass.data[DOMAIN]["medications"]

    def set_all(self, data):
        """
        Replace entire medication dataset.
        """
        self.hass.data[DOMAIN]["medications"] = data

    def get_med(self, med_id):
        """
        Get a single medication by ID.
        """
        return self.hass.data[DOMAIN]["medications"].get(med_id)

    def update_med(self, med_id, med_data):
        """
        Update or create a medication entry.
        """
        self.hass.data[DOMAIN]["medications"][med_id] = med_data

    # ---------------------------------------------------------
    # NEW FUNCTION: mark medication as taken
    # ---------------------------------------------------------
    def mark_taken(self, med_id, timestamp):
        """
        Mark a medication as taken.

        This updates:
        - last_taken timestamp

        This is the core mutation point for the system.
        """

        # Get existing medication entry
        med = self.get_med(med_id)

        # If medication does not exist, do nothing safely
        if not med:
            return

        # Update last_taken timestamp
        med["last_taken"] = timestamp

        # Save updated record back into storage
        self.update_med(med_id, med)
