"""Medication Engine (core scheduler loop).

This engine continuously evaluates medication schedules and determines:
- not_due
- due_soon
- due
- overdue
"""

import asyncio
from datetime import datetime, timezone

from homeassistant.core import HomeAssistant

from .storage import MedStorage  # Storage layer (single source of truth)


class MedEngine:
    """
    Core medication scheduling engine.

    This runs continuously and evaluates medication timing state.
    """

    def __init__(self, hass: HomeAssistant):
        # Home Assistant instance reference
        self.hass = hass

        # Controls whether engine loop is running
        self.running = False

        # Storage layer instance
        self.storage = MedStorage(hass)

    async def async_start(self):
        """
        Start the engine loop.
        """
        self.running = True

        # Start background async task
        self.hass.loop.create_task(self._run_loop())

    async def async_stop(self):
        """
        Stop the engine loop.
        """
        self.running = False

    async def _run_loop(self):
        """
        Continuous evaluation loop.

        Runs every 30 seconds while integration is active.
        """
        while self.running:

            try:
                self._tick()
            except Exception as err:
                print(f"[MED ENGINE ERROR] {err}")

            await asyncio.sleep(30)

    def _tick(self):
        """
        Single evaluation cycle.

        This evaluates all medications in storage.
        """

        # Current UTC time for all calculations
        now = datetime.now(timezone.utc)

        # Load all medications from storage
        meds = self.storage.get_all()

        # If no medications exist, exit safely
        if not meds:
            print("[MED ENGINE] No medications found.")
            return

        # Evaluate each medication
        for med_id, med in meds.items():

            status = self._calculate_status(med, now)

            print(f"[MED ENGINE] {med_id} -> {status}")

    def _calculate_status(self, med, now):
        """
        Determine medication state using improved logic.
        """

        # Last time medication was taken
        last_taken = med.get("last_taken")

        # Dose interval in hours
        interval_hours = med.get("interval_hours")

        # If medication has never been taken
        if not last_taken:
            return "not_initialized"

        # Convert interval to seconds
        interval_seconds = interval_hours * 3600

        # Compute next due timestamp
        next_due = last_taken + interval_seconds

        # Time difference between now and next dose
        time_to_due = next_due - now.timestamp()

        # ---------------------------------------------------------
        # STATE LOGIC
        # ---------------------------------------------------------

        # If we're past the due time by more than 1 hour
        if time_to_due < -3600:
            return "overdue"

        # If we are past or at due time
        if time_to_due <= 0:
            return "due"

        # If medication is due within next 60 minutes
        if time_to_due <= 3600:
            return "due_soon"

        # Otherwise still safely scheduled
        return "not_due"
