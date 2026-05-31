"""Medication Engine (core scheduler loop).

This file is the complete working engine for HA Meds Manager.

It is responsible for:
- loading medication data from storage
- evaluating medication schedules
- determining medication state (not_due / due_soon / due / overdue)
- triggering notifications via Home Assistant services
"""

import asyncio  # Used for continuous background loop timing

from datetime import datetime, timezone  # Used for time calculations

from homeassistant.core import HomeAssistant  # Home Assistant core system access

from .storage import MedStorage  # Storage layer (single source of truth for meds)


class MedEngine:
    """
    Core medication scheduling engine.

    This engine continuously runs in the background and:
    - evaluates medication timing
    - calculates next dose state
    - triggers notifications when needed
    """

    def __init__(self, hass: HomeAssistant):
        # Store Home Assistant instance reference
        self.hass = hass

        # Engine running flag (controls loop lifecycle)
        self.running = False

        # Initialize storage layer (access to medication data)
        self.storage = MedStorage(hass)

    async def async_start(self):
        """
        Start the background engine loop.
        """

        # Set engine state to running
        self.running = True

        # Create async task inside Home Assistant event loop
        self.hass.loop.create_task(self._run_loop())

    async def async_stop(self):
        """
        Stop the engine loop safely.
        """

        # Set running flag to false (loop will exit naturally)
        self.running = False

    async def _run_loop(self):
        """
        Main continuous loop.

        Runs indefinitely while integration is active.
        """

        while self.running:

            try:
                # Execute one evaluation cycle
                self._tick()

            except Exception as err:
                # Catch unexpected errors so engine never crashes HA
                print(f"[MED ENGINE ERROR] {err}")

            # Delay between evaluation cycles
            await asyncio.sleep(30)

    def _tick(self):
        """
        Single evaluation cycle.

        This processes all medications and determines their state.
        """

        # ---------------------------------------------------------
        # TIME SOURCE
        # ---------------------------------------------------------

        # Current UTC timestamp used for all comparisons
        now = datetime.now(timezone.utc)

        # ---------------------------------------------------------
        # LOAD DATA
        # ---------------------------------------------------------

        # Retrieve all medications from storage layer
        meds = self.storage.get_all()

        # If no medications exist, exit safely
        if not meds:
            print("[MED ENGINE] No medications found.")
            return

        # ---------------------------------------------------------
        # PROCESS EACH MEDICATION
        # ---------------------------------------------------------

        for med_id, med in meds.items():

            # -----------------------------------------------------
            # STATE CALCULATION
            # -----------------------------------------------------

            status = self._calculate_status(med, now)

            # Debug output for development visibility
            print(f"[MED ENGINE] {med_id} -> {status}")

            # -----------------------------------------------------
            # NOTIFICATION LOGIC
            # -----------------------------------------------------

            # If medication requires attention, trigger alert
            if status in ["due", "due_soon", "overdue"]:

                self._send_notification(med_id, med, status)

    def _calculate_status(self, med, now):
        """
        Determine medication state based on schedule rules.
        """

        # ---------------------------------------------------------
        # INPUT DATA
        # ---------------------------------------------------------

        # Last time medication was taken (timestamp)
        last_taken = med.get("last_taken")

        # Interval between doses in hours
        interval_hours = med.get("interval_hours")

        # ---------------------------------------------------------
        # VALIDATION STATE
        # ---------------------------------------------------------

        # If medication has never been taken
        if not last_taken:
            return "not_initialized"

        # If interval is missing or invalid
        if not interval_hours:
            return "invalid_interval"

        # ---------------------------------------------------------
        # TIME CALCULATION
        # ---------------------------------------------------------

        # Convert hours to seconds for calculation
        interval_seconds = interval_hours * 3600

        # Calculate next scheduled dose time
        next_due = last_taken + interval_seconds

        # Calculate time difference from now
        time_to_due = next_due - now.timestamp()

        # ---------------------------------------------------------
        # STATE LOGIC
        # ---------------------------------------------------------

        # If overdue beyond 1 hour
        if time_to_due < -3600:
            return "overdue"

        # If currently due or slightly late
        if time_to_due <= 0:
            return "due"

        # If due within next hour
        if time_to_due <= 3600:
            return "due_soon"

        # Otherwise medication is safely scheduled
        return "not_due"

    def _send_notification(self, med_id, med, status):
        """
        Send notification via Home Assistant.

        Currently uses persistent notifications.
        Future upgrade: mobile_app push notifications.
        """

        # Get human-readable medication name
        name = med.get("name", med_id)

        # Build notification message
        message = f"Medication '{name}' is {status}"

        # ---------------------------------------------------------
        # HOME ASSISTANT NOTIFICATION CALL
        # ---------------------------------------------------------

        self.hass.services.call(
            "persistent_notification",
            "create",
            {
                "title": "Medication Reminder",
                "message": message
            }
        )

        # Debug log for development
        print(f"[MED NOTIFY] {med_id} -> {status}")
