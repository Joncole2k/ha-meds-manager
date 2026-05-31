"""Medication Engine (core scheduler loop).

This file is the complete working engine for HA Meds Manager.

It is responsible for:
- loading medication data from storage
- evaluating medication schedules
- determining medication state (not_due / due_soon / due / overdue)
- handling snooze logic
- preventing notification spam
- triggering notifications via Home Assistant services
"""

import asyncio  # Used for continuous background loop timing

from datetime import datetime, timezone  # Used for time calculations

from homeassistant.core import HomeAssistant  # Home Assistant system access

from .storage import MedStorage  # Storage layer (single source of truth for meds)


class MedEngine:
    """
    Core medication scheduling engine.

    This engine continuously runs in the background and:
    - evaluates medication timing
    - calculates next dose state
    - handles snooze logic
    - triggers notifications when needed
    """

    def __init__(self, hass: HomeAssistant):
        # Store Home Assistant instance reference
        self.hass = hass

        # Engine running flag (controls loop lifecycle)
        self.running = False

        # Initialize storage layer
        self.storage = MedStorage(hass)

    # ---------------------------------------------------------
    # ENGINE LIFECYCLE
    # ---------------------------------------------------------

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

        # Set running flag to false
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
                # Prevent crash of Home Assistant
                print(f"[MED ENGINE ERROR] {err}")

            # Delay between evaluation cycles
            await asyncio.sleep(30)

    # ---------------------------------------------------------
    # MAIN ENGINE CYCLE
    # ---------------------------------------------------------

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

            # Save computed status back into storage (future UI support)
            med["status"] = status

            self.storage.update_med(med_id, med)

            # Debug output
            print(f"[MED ENGINE] {med_id} -> {status}")

            # -----------------------------------------------------
            # NOTIFICATION LOGIC
            # -----------------------------------------------------

            # Check if medication requires notification
            if self._should_notify(med, status, now):

                self._send_notification(med_id, med, status)

                # Update notification timestamp
                med["last_notified"] = now.timestamp()
                self.storage.update_med(med_id, med)

    # ---------------------------------------------------------
    # STATE CALCULATION
    # ---------------------------------------------------------

    def _calculate_status(self, med, now):
        """
        Determine medication state based on schedule rules.
        """

        # ---------------------------------------------------------
        # INPUT DATA
        # ---------------------------------------------------------

        # Last time medication was taken
        last_taken = med.get("last_taken")

        # Dose interval in hours
        interval_hours = med.get("interval_hours")

        # Snooze timestamp (if any)
        snooze_until = med.get("snooze_until")

        # ---------------------------------------------------------
        # VALIDATION STATE
        # ---------------------------------------------------------

        if not last_taken:
            return "not_initialized"

        if not interval_hours:
            return "invalid_interval"

        # ---------------------------------------------------------
        # SNOOZE LOGIC
        # ---------------------------------------------------------

        # If snoozed and still active
        if snooze_until and now.timestamp() < snooze_until:
            return "snoozed"

        # ---------------------------------------------------------
        # TIME CALCULATION
        # ---------------------------------------------------------

        interval_seconds = interval_hours * 3600

        next_due = last_taken + interval_seconds

        time_to_due = next_due - now.timestamp()

        # ---------------------------------------------------------
        # STATE LOGIC
        # ---------------------------------------------------------

        if time_to_due < -3600:
            return "overdue"

        if time_to_due <= 0:
            return "due"

        if time_to_due <= 3600:
            return "due_soon"

        return "not_due"

    # ---------------------------------------------------------
    # NOTIFICATION CONTROL (ANTI-SPAM LOGIC)
    # ---------------------------------------------------------

    def _should_notify(self, med, status, now):
        """
        Determines whether notification should be sent.
        """

        if status not in ["due", "due_soon", "overdue"]:
            return False

        last_notified = med.get("last_notified")

        if not last_notified:
            return True

        # 15 minute cooldown
        return (now.timestamp() - last_notified) > 900

    # ---------------------------------------------------------
    # NOTIFICATION SYSTEM
    # ---------------------------------------------------------

    def _send_notification(self, med_id, med, status):
        """
        Send notification via Home Assistant.

        Current: persistent notifications
        Future: mobile_app, SMS, voice assistants
        """

        name = med.get("name", med_id)

        message = f"Medication '{name}' is {status}"

        # Home Assistant notification call
        self.hass.services.call(
            "persistent_notification",
            "create",
            {
                "title": "Medication Reminder",
                "message": message
            }
        )

        print(f"[MED NOTIFY] {med_id} -> {status}")
