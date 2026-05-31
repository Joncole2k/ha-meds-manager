# HA Meds Manager Architecture

## Purpose

HA Meds Manager is a Home Assistant integration for:

- Medication scheduling
- Medication reminders
- Snoozing reminders
- Inventory tracking
- Dose history tracking
- Multi-person medication management

## Core Design

One medication regimen is represented by one Home Assistant entity.

Entity format:

sensor.med_<person_id>_<med_id>

Example:

sensor.med_jonathan_001

The entity contains medication information and status through attributes.

The integration engine is the source of truth for all medication state.
