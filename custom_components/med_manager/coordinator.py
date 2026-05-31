"""Medication Engine (core scheduler loop).

This is the brain of the system.

It is responsible for:
- continuously evaluating medication schedules
- determining due / not due states
- logging status updates
"""

import asyncio
from datetime import datetime, timezone

from homeassistant.core import HomeAssistant

from .storage import MedStorage  # Import storage layer


class MedEngine:
    """
    Core medication scheduling engine.

    This runs continuously and evaluates medication state
    from persistent storage.
    """

    def __init__(self, hass: HomeAssistant):
        # Reference to Home Assistant core instance
        self.hass = hass

        # Flag controlling engine loop execution
        self.running = False

        # Initialize storage layer (single source of truth)
        self.storage = MedStorage(hass)

    async def async_start(self):
        """
        Start the engine background loop.
        """
        self.running = True

        # Start async loop task inside Home Assistant event loop
        self.hass.loop.create_task(self._run_loop())

    async def async_stop(self):
        """
        Stop the engine loop safely.
        """
        self.running = False

    async def _run_loop(self):
        """
        Continuous evaluation loop.

        Runs forever while integration is active.
        """
        while self.running:

            try:
                self._tick()
            except Exception as err:
                print(f"[MED ENGINE ERROR] {err}")

            # Engine cycle delay (we will tune later)
            await asyncio.sleep(30)

    def _tick(self):
        """
        Single evaluation cycle.

        This processes ALL medications in storage.
        """

        # Current UTC time used for all calculations
        now = datetime.now(timezone.utc)

        # Load real medication data from storage
        meds = self.storage.get_all()

        # If no medications exist, safely do nothing
        if not meds:
            print("[MED ENGINE] No medications found in storage.")
            return

        # Evaluate each medication entry
        for med_id, med in meds.items():

            status = self._calculate_status(med, now)

            # Debug output (temporary until entity system is built)
            print(f"[MED ENGINE] {med_id} -> {status}")

    def _calculate_status(self, med, now):
        """
        Calculate medication state based on schedule.
        """

        # Last time medication was taken
        last_taken = med.get("last_taken")

        # Interval between doses (hours)
        interval_hours = med.get("interval_hours")

        # If no last_taken exists, medication is not initialized
        if not last_taken:
            return "not_initialized"

        # Compute next due timestamp
        next_due = last_taken + (interval_hours * 3600)

        # Determine if medication is due
        if now.timestamp() >= next_due:
            return "due"

        return "not_due"
