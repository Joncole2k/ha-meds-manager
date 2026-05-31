"""
HA Meds Manager - Config Flow (UI Setup + Medication Creator)

===========================================================
PURPOSE
===========================================================
This file defines the Home Assistant UI setup flow.

It is responsible for:
- Initial integration setup in HA UI
- Providing "Add Medication" wizard
- Creating medication entries in storage

===========================================================
ARCHITECTURE ROLE
===========================================================
This is the USER INTERFACE LAYER for setup:

UI → Config Flow → Storage → Engine → Entities

===========================================================
"""

# ---------------------------------------------------------
# HOME ASSISTANT CONFIG FLOW IMPORTS
# ---------------------------------------------------------
import voluptuous as vol  # schema validation for UI forms

from homeassistant import config_entries  # base config flow system

# ---------------------------------------------------------
# LOCAL INTEGRATION IMPORTS
# ---------------------------------------------------------
from .storage import MedStorage  # shared medication storage layer

# ---------------------------------------------------------
# DOMAIN IDENTIFIER
# ---------------------------------------------------------
DOMAIN = "med_manager"


# =========================================================
# CONFIG FLOW CLASS (MAIN ENTRY POINT FOR UI)
# =========================================================
class MedManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """
    Handles UI setup and medication creation wizard.
    """

    # -----------------------------------------------------
    # VERSION TRACKING
    # -----------------------------------------------------
    VERSION = 1

    # -----------------------------------------------------
    # INITIALIZATION
    # -----------------------------------------------------
    def __init__(self):
        # Storage reference (initialized when needed)
        self._storage = None

    # =====================================================
    # STEP 1 - MAIN MENU
    # =====================================================
    async def async_step_user(self, user_input=None):
        """
        First screen shown in HA UI.

        Lets user choose:
        - Add Medication
        - Finish setup
        """

        # -------------------------------------------------
        # INIT STORAGE (LAZY LOAD)
        # -------------------------------------------------
        if self._storage is None:
            self._storage = MedStorage(self.hass)

        # -------------------------------------------------
        # HANDLE USER INPUT
        # -------------------------------------------------
        if user_input is not None:

            # USER SELECTED: ADD MEDICATION
            if user_input["action"] == "add_medication":
                return await self.async_step_add_medication()

            # USER SELECTED: FINISH
            return self.async_create_entry(
                title="HA Meds Manager",
                data={}
            )

        # -------------------------------------------------
        # UI FORM DEFINITION (MAIN MENU)
        # -------------------------------------------------
        schema = vol.Schema({
            vol.Required("action", default="add_medication"): vol.In({
                "add_medication": "Add Medication",
                "finish": "Finish Setup"
            })
        })

        # -------------------------------------------------
        # RENDER FORM
        # -------------------------------------------------
        return self.async_show_form(
            step_id="user",
            data_schema=schema
        )

    # =====================================================
    # STEP 2 - ADD MEDICATION FORM
    # =====================================================
    async def async_step_add_medication(self, user_input=None):
        """
        Medication creation form.

        This creates:
        - storage entry
        - engine-visible medication
        - entity-ready dataset
        """

        # -------------------------------------------------
        # HANDLE FORM SUBMISSION
        # -------------------------------------------------
        if user_input is not None:

            # -------------------------------------------------
            # MEDICATION ID (PRIMARY KEY)
            # -------------------------------------------------
            med_id = user_input["med_id"]

            # -------------------------------------------------
            # BUILD MEDICATION DATA STRUCTURE
            # -------------------------------------------------
            data = {
                # -------------------------------
                # IDENTITY LAYER
                # -------------------------------
                "common_name": user_input["common_name"],
                "generic_name": user_input.get("generic_name"),
                "brand_name": user_input.get("brand_name"),
                "person": user_input["person"],

                # -------------------------------
                # SCHEDULING LAYER
                # -------------------------------
                "interval_hours": user_input["interval_hours"],
                "last_taken": None,
                "next_due": None,

                # -------------------------------
                # ENGINE STATE
                # -------------------------------
                "status": "not_initialized",
                "should_notify": False,

                # -------------------------------
                # USER STATE
                # -------------------------------
                "snooze_until": None,

                # -------------------------------
                # NOTIFICATION STATE
                # -------------------------------
                "last_notified": None,
                "notification_count": 0,

                # -------------------------------
                # INVENTORY STATE
                # -------------------------------
                "current_count": user_input.get("current_count", 0),
                "low_stock_threshold": user_input.get("low_stock_threshold", 5),
                "refill_required": False,
            }

            # -------------------------------------------------
            # STORE MEDICATION
            # -------------------------------------------------
            storage = MedStorage(self.hass)
            storage.create_medication(med_id, data)

            # -------------------------------------------------
            # FINISH FLOW
            # -------------------------------------------------
            return self.async_create_entry(
                title=f"Medication Added: {med_id}",
                data={}
            )

        # -------------------------------------------------
        # UI FORM (MEDICATION INPUT)
        # -------------------------------------------------
        schema = vol.Schema({
            # -------------------------------
            # REQUIRED FIELDS
            # -------------------------------
            vol.Required("med_id"): str,
            vol.Required("common_name"): str,
            vol.Required("person"): str,
            vol.Required("interval_hours"): int,

            # -------------------------------
            # OPTIONAL FIELDS
            # -------------------------------
            vol.Optional("generic_name"): str,
            vol.Optional("brand_name"): str,

            vol.Optional("current_count", default=0): int,
            vol.Optional("low_stock_threshold", default=5): int,
        })

        # -------------------------------------------------
        # RENDER FORM
        # -------------------------------------------------
        return self.async_show_form(
            step_id="add_medication",
            data_schema=schema
        )
