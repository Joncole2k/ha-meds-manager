"""Storage layer for HA Meds Manager.

This module handles persistent medication data storage.
For now we use hass.data (in-memory but persistent during runtime).
Later we will upgrade to Home Assistant Store API.
"""


DOMAIN = "med_manager"


class MedStorage:
    """
    Simple storage wrapper around hass.data.

    This is the single source of truth for medication data.
    """

    def __init__(self, hass):
        # Reference to Home Assistant instance
        self.hass = hass

        # Ensure storage container exists
        self.hass.data.setdefault(DOMAIN, {})

        # Create internal storage bucket
        self.hass.data[DOMAIN].setdefault("medications", {})

    def get_all(self):
        """
        Return all medication entries.
        """
        return self.hass.data[DOMAIN]["medications"]

    def set_all(self, data):
        """
        Replace entire medication dataset.
        """
        self.hass.data[DOMAIN]["medications"] = data

    def update_med(self, med_id, med_data):
        """
        Update a single medication entry.
        """
        self.hass.data[DOMAIN]["medications"][med_id] = med_data

    def get_med(self, med_id):
        """
        Get a single medication entry.
        """
        return self.hass.data[DOMAIN]["medications"].get(med_id)
