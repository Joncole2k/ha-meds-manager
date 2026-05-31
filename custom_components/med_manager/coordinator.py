"""HA Meds Manager - Final Medication Engine

This file is the CORE EXECUTION ENGINE for the entire system.

It is responsible for:

===========================================================
SCHEDULING SYSTEM
===========================================================
- calculating next dose timing
- handling rolling schedule (prevents drift errors)
- supporting interval-based medication logic

===========================================================
USER BEHAVIOR SYSTEMS
===========================================================
- marking medication as taken
- snooze-aware evaluation
- refill / inventory awareness

===========================================================
NOTIFICATION SYSTEM
===========================================================
- persistent notification triggering
- anti-spam cooldown logic
- state-based alerts (due, overdue, due_soon)

===========================================================
AUTOMATION / EVENT SYSTEM
===========================================================
- emits lifecycle events for future integrations
- supports entity system binding (sensor.med_*)

===========================================================
UI / DASHBOARD SYSTEM
===========================================================
- updates status fields used by Lovelace entities
- prepares structured state output
"""

import asyncio  # async loop for continuous execution

from datetime import datetime, timezone  # time calculations

from homeassistant.core import HomeAssistant  # HA system access

from .storage import MedStorage  # central data source


# ---------------------------------------------------------
# DOMAIN IDENTIFIER
# ---------------------------------------------------------
DOMAIN = "med_manager"


class MedEngine:
    """
    Final production-ready medication engine.

    This engine runs continuously and is responsible for:
    - evaluating medication state
    - updating storage state
    - triggering notifications
    - emitting automation events
    """

    def __init__(self, hass: HomeAssistant):
        # Home Assistant instance reference
        self.hass = hass

        # Engine lifecycle flag
        self.running = False

        # Storage connection
        self.storage = MedStorage(hass)

    # ---------------------------------------------------------
    # ENGINE LIFECYCLE
    # ---------------------------------------------------------

    async def async_start(self):
        """Start engine loop."""

        self.running = True
        self.hass.loop.create_task(self._run_loop())

    async def async_stop(self):
        """Stop engine loop."""

        self.running = False

    async def _run_loop(self):
        """Main continuous evaluation loop."""

        while self.running:

            try:
                self._tick()

            except Exception as err:
                # Never crash Home Assistant
                print(f"[MED ENGINE ERROR] {err}")

            await asyncio.sleep(30)

    # ---------------------------------------------------------
    # MAIN ENGINE CYCLE
    # ---------------------------------------------------------

    def _tick(self):
        """
        Evaluate all medications in system.
        """

        # ---------------------------------------------------------
        # TIME SOURCE
        # ---------------------------------------------------------

        now = datetime.now(timezone.utc)

        # ---------------------------------------------------------
        # LOAD DATA
        # ---------------------------------------------------------

        meds = self.storage.get_all()

        if not meds:
            print("[MED ENGINE] No medications found.")
            return

        # ---------------------------------------------------------
        # PROCESS EACH MEDICATION
        # ---------------------------------------------------------

        for med_id, med in meds.items():

            # Evaluate full medication state
            state = self._evaluate(med, now)

            # Persist engine results into storage (UI + entity layer)
            med["status"] = state["status"]
            med["next_due"] = state["next_due"]

            self.storage.update_med(med_id, med)

            # Debug output
            print(f"[MED ENGINE] {med_id} -> {state['status']}")

            # -----------------------------------------------------
            # EVENT EMISSION (FUTURE AUTOMATIONS)
            # -----------------------------------------------------

            self._emit_event(med_id, state)

            # -----------------------------------------------------
            # NOTIFICATION SYSTEM
            # -----------------------------------------------------

            if state["should_notify"]:
                self._notify(med_id, med, state["status"])

                # update notification tracking
                self.storage.mark_notified(med_id, now.timestamp())

    # ---------------------------------------------------------
    # CORE EVALUATION ENGINE
    # ---------------------------------------------------------

    def _evaluate(self, med, now):
        """
        Compute full medication state.

        Output is structured for:
        - engine decisions
        - UI entities
        - automations
        """

        # ---------------------------------------------------------
        # INPUT DATA
        # ---------------------------------------------------------

        last_taken = med.get("last_taken")
        interval_hours = med.get("interval_hours")
        snooze_until = med.get("snooze_until")
        last_notified = med.get("last_notified")
        current_count = med.get("current_count", 0)
        low_stock_threshold = med.get("low_stock_threshold", 0)

        # Default response structure
        result = {
            "status": "unknown",
            "next_due": None,
            "should_notify": False,
            "refill_flag": False
        }

        # ---------------------------------------------------------
        # VALIDATION
        # ---------------------------------------------------------

        if not last_taken or not interval_hours:
            result["status"] = "not_initialized"
            return result

        # ---------------------------------------------------------
        # INVENTORY CHECK
        # ---------------------------------------------------------

        if current_count <= low_stock_threshold:
            result["refill_flag"] = True

        # ---------------------------------------------------------
        # SNOOZE SYSTEM
        # ---------------------------------------------------------

        if snooze_until and now.timestamp() < snooze_until:
            result["status"] = "snoozed"
            result["next_due"] = last_taken + (interval_hours * 3600)
            return result

        # ---------------------------------------------------------
        # SCHEDULING SYSTEM (ROLLING MODEL)
        # ---------------------------------------------------------

        interval_seconds = interval_hours * 3600
        next_due = last_taken + interval_seconds

        result["next_due"] = next_due

        time_to_due = next_due - now.timestamp()

        # ---------------------------------------------------------
        # STATE CLASSIFICATION
        # ---------------------------------------------------------

        if time_to_due < -3600:
            result["status"] = "overdue"

        elif time_to_due <= 0:
            result["status"] = "due"

        elif time_to_due <= 3600:
            result["status"] = "due_soon"

        else:
            result["status"] = "not_due"

        # ---------------------------------------------------------
        # NOTIFICATION GATING (ANTI-SPAM)
        # ---------------------------------------------------------

        if result["status"] in ["due", "due_soon", "overdue"]:

            if not last_notified:
                result["should_notify"] = True

            else:
                if now.timestamp() - last_notified > 900:
                    result["should_notify"] = True

        return result

    # ---------------------------------------------------------
    # NOTIFICATION SYSTEM
    # ---------------------------------------------------------

    def _notify(self, med_id, med, status):
        """
        Send Home Assistant notification.
        """

        name = med.get("name", med_id)

        message = f"Medication '{name}' is {status}"

        self.hass.services.call(
            "persistent_notification",
            "create",
            {
                "title": "Medication Reminder",
                "message": message
            }
        )

        print(f"[MED NOTIFY] {med_id} -> {status}")

    # ---------------------------------------------------------
    # EVENT SYSTEM (FUTURE AUTOMATIONS / ENTITIES)
    # ---------------------------------------------------------

    def _emit_event(self, med_id, state):
        """
        Emits structured event for future:
        - automations
        - entity sync
        - dashboard updates
        """

        event_type = f"med_manager_{state['status']}"

        self.hass.bus.fire(
            event_type,
            {
                "med_id": med_id,
                "status": state["status"],
                "next_due": state["next_due"],
                "refill_flag": state.get("refill_flag", False)
            }
        )
