from homeassistant import config_entries
import voluptuous as vol

DOMAIN = "med_manager"


class MedManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Med Manager."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="HA Meds Manager",
                data={}
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({})
        )
