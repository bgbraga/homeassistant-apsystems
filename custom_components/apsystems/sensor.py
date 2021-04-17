import logging
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.sun import get_astral_event_date
from homeassistant.util.dt import utcnow as dt_utcnow, as_local
import voluptuous as vol
from datetime import timedelta

CONF_IP_ADDRESS = 'ip_address'
CONF_NAME = 'name'
POWER_UNIT = "kWh"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_IP_ADDRESS): cv.string,
    vol.Optional(CONF_NAME, default='APsystems'): cv.string
})
from homeassistant.const import (
    CONF_MONITORED_CONDITIONS, CONF_NAME, CONF_SCAN_INTERVAL, ATTR_ATTRIBUTION, SUN_EVENT_SUNRISE, SUN_EVENT_SUNSET
    )

DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)
_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    name = config.get(CONF_NAME)
    ip_address = config[CONF_IP_ADDRESS]

    sensor = ApsystemsSensor(name, ip_address)
    async_add_entities([sensor])


class ApsystemsSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, name, ip_address):
        """Initialize the sensor."""
        self._state = None
        self._name = name
        self._ip_address = ip_address

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return POWER_UNIT

    @property
    def available(self, utcnow=None):
        if utcnow is None:
            utcnow = dt_utcnow()
        now = as_local(utcnow)

        start_time = self.find_start_time(now)
        stop_time = self.find_stop_time(now)

        _LOGGER.debug("!!! Start Time, Stop Time, Name: {}, {}, {}".format(as_local(start_time), as_local(stop_time), self._name))

        return True

    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = 23

    def find_start_time(self, now):
        """Return sunrise or start_time if given."""
        sunrise = get_astral_event_date(self.hass, SUN_EVENT_SUNRISE, now.date())
        return sunrise

    def find_stop_time(self, now):
        """Return sunset or stop_time if given."""
        sunset = get_astral_event_date(self.hass, SUN_EVENT_SUNSET, now.date())
        return sunset