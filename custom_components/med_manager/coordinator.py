"""Medication Engine (core scheduler loop).

This file is the core brain of HA Meds Manager.

It is responsible for:
- continuously evaluating medication schedules
- reading medication data from storage
- determining medication states (due / not_due / overdue)
"""

import asyncio  # Used for running continuous background loop

from datetime import datetime, timezone  # Used for time-based calculations

from homeassistant.core import HomeAssistant  # Home Assistant core reference

from .storage import MedStorage  # Import storage layer (single source of truth)


class MedEngine:
    """
    Core medication scheduling engine.

    This engine continuously evaluates medication timing
    and produces status updates.
    """

    def __init__(self, hass: HomeAssistant):
        # Store Home Assistant instance reference
        self.hass = hass

        # Flag controlling whether engine loop is running
        self.running = False

        # Initialize storage layer
        self.storage = MedStorage(hass)

    async def async_start(self):
        """
        Starts the background engine loop.
        """

        # Set running flag to true
        self.running = True

        # Start async background loop inside Home Assistant event loop
        self.hass.loop.create_task(self._run_loop())

    async def async_stop(self):
        """
        Stops the engine loop safely.
        """

        # Set running flag to false to exit loop
        self.running = False

    async def _run_loop(self):
        """
        Main continuous execution loop.

        This runs indefinitely while the integration is active.
        """

        while self.running:

            try:
                # Run one evaluation cycle
                self._tick()

            except Exception as err:
                # Catch and log any engine errors
                print(f"[MED ENGINE ERROR] {err}")

            # Wait before next evaluation cycle
            await asyncio.sleep(30)

    def _tick(self):
        """
        Single evaluation cycle.

        This processes all medications and computes their state.
        """

        # Get current UTC time for all calculations
        now = datetime.now(timezone.utc)

        # Retrieve all medication data from storage
        meds = self.storage.get_all()

        # If no medications exist, exit safely
        if not meds:
            print("[MED ENGINE] No medications found.")
            return

        # Loop through each medication entry
        for med_id, med in meds.items():

            # Calculate current status for this medication
            status = self._calculate_status(med, now)

            # Debug output for development visibility
            print(f"[MED ENGINE] {med_id} -> {status}")

    def _calculate_status(self, med, now):
        """
        Determines medication state based on timing rules.
        """

        # Retrieve last taken timestamp (if exists)
        last_taken = med.get("last_taken")

        # Retrieve dosing interval in hours
        interval_hours = med.get("interval_hours")

        # If medication has never been taken
        if not last_taken:
            return "not_initialized"

        # Convert interval to seconds for calculation
        interval_seconds = interval_hours * 3600

        # Compute next scheduled dose time
        next_due = last_taken + interval_seconds

        # Compute time difference between now and next dose
        time_to_due = next_due - now.timestamp()

        # ---------------------------------------------------------
        # STATE LOGIC
        # ---------------------------------------------------------

        # If overdue by more than 1 hour
        if time_to_due < -3600:
            return "overdue"

        # If currently due or slightly past due
        if time_to_due <= 0:
            return "due"

        # If due within next hour
        if time_to_due <= 3600:
            return "due_soon"

        # Otherwise medication is not due yet
        return "not_due"
