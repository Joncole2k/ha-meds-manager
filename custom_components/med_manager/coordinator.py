"""Medication Engine (core scheduler loop).

This is the brain of the system.
It will:
- continuously evaluate medication schedules
- calculate next dose times
- determine due / not due / snoozed states
"""

import asyncio
from datetime import datetime, timezone

from homeassistant.core import HomeAssistant


class MedEngine:
    """
    Core medication scheduling engine.

    Runs continuously in the background and evaluates medication state.
    """

    def __init__(self, hass: HomeAssistant):
        # Reference to Home Assistant instance
        self.hass = hass

        # Controls whether the engine loop is running
        self.running = False

        # In-memory placeholder for medication data (temporary)
        self.data = {}

    async def async_start(self):
        """
        Called by __init__.py to start the engine.
        """
        self.running = True

        # Start background loop task
        self.hass.loop.create_task(self._run_loop())

    async def async_stop(self):
        """Stops the engine loop."""
        self.running = False

    async def _run_loop(self):
        """
        Main engine loop.

        Runs forever (until stopped) and recalculates medication states.
        """
        while self.running:

            try:
                self._tick()
            except Exception as err:
                print(f"[MED ENGINE ERROR] {err}")

            # Engine update interval (we will tune later)
            await asyncio.sleep(30)

    def _tick(self):
        """
        Single evaluation cycle.

        This is where ALL medication logic will eventually live.
        """

        now = datetime.now(timezone.utc)

        # TEMP: mock data until storage layer is built
        meds = self._load_mock_data()

        for med_id, med in meds.items():

            status = self._calculate_status(med, now)

            print(f"[MED ENGINE] {med_id} -> {status}")

    def _calculate_status(self, med, now):
        """
        Basic placeholder logic for medication state.
        """

        last_taken = med["last_taken"]
        interval_hours = med["interval_hours"]

        if not last_taken:
            return "not_initialized"

        next_due = last_taken + (interval_hours * 3600)

        if now.timestamp() >= next_due:
            return "due"

        return "not_due"

    def _load_mock_data(self):
        """
        Temporary data source.

        Will be replaced by persistent storage in next step.
        """

        now = datetime.now(timezone.utc)

        return {
            "jonathan_001": {
                "last_taken": now.timestamp() - 7200,  # 2 hours ago
                "interval_hours": 6
            }
        }
