/*
===========================================================
HA Meds Manager - Lovelace Card (HACS-COMPATIBLE FINAL)
===========================================================

This is the UI CONTROL LAYER for HA Meds Manager.

It is designed to work with:
- Home Assistant Lovelace
- HACS distribution (future-ready)
- Mushroom / Mod Card dashboards (entity-driven compatibility)

===========================================================
PRINCIPLES
===========================================================
✔ Uses Home Assistant theme variables (NO hardcoded colors)
✔ Works with sensor.med_* entities
✔ Stateless rendering (reacts to hass updates)
✔ Calls backend services only (no local logic duplication)
✔ Safe for HACS distribution
*/

class MedManagerCard extends HTMLElement {

    // ---------------------------------------------------------
    // CARD CONFIGURATION
    // ---------------------------------------------------------

    setConfig(config) {
        // Store user-defined config (entity selection, options, etc.)
        this.config = config;
    }

    // ---------------------------------------------------------
    // HOME ASSISTANT STATE UPDATE ENTRY POINT
    // ---------------------------------------------------------

    set hass(hass) {
        // Save HA reference
        this._hass = hass;

        // Re-render whenever state updates
        this.render();
    }

    // ---------------------------------------------------------
    // MAIN RENDER FUNCTION
    // ---------------------------------------------------------

    render() {

        // Ensure HA + config exist
        if (!this._hass || !this.config) return;

        const entityId = this.config.entity;
        const stateObj = this._hass.states[entityId];

        // Handle missing entity gracefully
        if (!stateObj) {
            this.innerHTML = `
                <div style="padding:12px;">
                    Entity not found: ${entityId}
                </div>
            `;
            return;
        }

        // Extract state + attributes
        const state = stateObj.state;
        const attrs = stateObj.attributes;

        // ---------------------------------------------------------
        // UI CONTAINER (THEME-COMPATIBLE)
        // ---------------------------------------------------------

        this.innerHTML = `
            <div style="
                padding: 16px;
                border-radius: 12px;

                /* Home Assistant theme compatibility */
                background: var(--card-background-color);
                color: var(--primary-text-color);
                border: 1px solid var(--divider-color);

                font-family: var(--primary-font-family);
            ">

                <!-- HEADER -->
                <div style="font-size: 18px; font-weight: 600;">
                    💊 ${attrs.name || entityId}
                </div>

                <!-- STATUS -->
                <div style="margin-top: 6px;">
                    Status:
                    <span style="font-weight: 600; color: var(--primary-color);">
                        ${state}
                    </span>
                </div>

                <!-- NEXT DOSE -->
                <div style="margin-top: 6px; font-size: 13px; opacity: 0.8;">
                    Next Due:
                    ${attrs.next_due
                        ? new Date(attrs.next_due * 1000).toLocaleString()
                        : "N/A"
                    }
                </div>

                <!-- INVENTORY -->
                <div style="margin-top: 6px; font-size: 13px;">
                    Inventory:
                    ${attrs.current_count ?? "?"}
                    ${attrs.refill_required ? "⚠️ LOW" : ""}
                </div>

                <!-- SNOOZE STATE -->
                <div style="margin-top: 6px; font-size: 12px; opacity: 0.7;">
                    Snooze Until:
                    ${attrs.snooze_until
                        ? new Date(attrs.snooze_until * 1000).toLocaleString()
                        : "None"
                    }
                </div>

                <!-- ACTION BUTTONS -->
                <div style="
                    margin-top: 14px;
                    display: flex;
                    gap: 8px;
                    flex-wrap: wrap;
                ">

                    <!-- TAKE BUTTON -->
                    <button
                        data-action="take"
                        data-entity="${entityId}"
                        style="padding: 6px 10px; cursor: pointer;"
                    >
                        Taken
                    </button>

                    <!-- SNOOZE BUTTON (1H) -->
                    <button
                        data-action="snooze"
                        data-minutes="60"
                        data-entity="${entityId}"
                        style="padding: 6px 10px; cursor: pointer;"
                    >
                        Snooze 1h
                    </button>

                    <!-- SNOOZE BUTTON (6H) -->
                    <button
                        data-action="snooze"
                        data-minutes="360"
                        data-entity="${entityId}"
                        style="padding: 6px 10px; cursor: pointer;"
                    >
                        Snooze 6h
                    </button>

                    <!-- REFILL BUTTON -->
                    <button
                        data-action="refill"
                        data-entity="${entityId}"
                        style="padding: 6px 10px; cursor: pointer;"
                    >
                        Refill
                    </button>

                </div>

            </div>
        `;

        // ---------------------------------------------------------
        // EVENT BINDING (AFTER RENDER)
        // ---------------------------------------------------------

        this.querySelectorAll("button").forEach(btn => {

            btn.addEventListener("click", (e) => {

                const action = e.target.getAttribute("data-action");
                const entity = e.target.getAttribute("data-entity");

                // Extract med_id from sensor.med_xxx
                const medId = entity.replace("sensor.", "");

                // TAKE ACTION
                if (action === "take") {
                    this._callService("take", { med_id: medId });
                }

                // SNOOZE ACTION
                if (action === "snooze") {
                    const minutes = parseInt(e.target.getAttribute("data-minutes"));
                    this._callService("snooze", {
                        med_id: medId,
                        minutes: minutes
                    });
                }

                // REFILL ACTION
                if (action === "refill") {
                    this._callService("refill", { med_id: medId });
                }
            });
        });
    }

    // ---------------------------------------------------------
    // SERVICE CALL WRAPPER
    // ---------------------------------------------------------

    _callService(service, data) {
        if (!this._hass) return;

        this._hass.callService(
            "med_manager",
            service,
            data
        );
    }

    // ---------------------------------------------------------
    // CARD SIZE HINT (OPTIONAL)
    // ---------------------------------------------------------

    getCardSize() {
        return 3;
    }
}

// ---------------------------------------------------------
// REGISTER CUSTOM ELEMENT
// ---------------------------------------------------------

customElements.define("med-manager-card", MedManagerCard);
