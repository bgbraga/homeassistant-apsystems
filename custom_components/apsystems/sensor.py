import logging
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.sun import get_astral_event_date
from homeassistant.util.dt import utcnow as dt_utcnow, as_local
import voluptuous as vol
import pprint
import requests
from requests.adapters import HTTPAdapter
from datetime import datetime, timedelta, date

CONF_USERNAME = 'username'
CONF_PASSWORD = 'password'
CONF_ECU_ID = 'ecuId'
CONF_SYSTEM_ID = 'systemId'
CONF_NAME = 'name'
POWER_UNIT = "kWh"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_ECU_ID): cv.string,
    vol.Required(CONF_SYSTEM_ID): cv.string,
    vol.Optional(CONF_NAME, default='APsystems'): cv.string
})
from homeassistant.const import (
    CONF_MONITORED_CONDITIONS, CONF_NAME, CONF_SCAN_INTERVAL, ATTR_ATTRIBUTION, SUN_EVENT_SUNRISE, SUN_EVENT_SUNSET
    )

SCAN_INTERVAL = timedelta(seconds=300)
_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    sensor_name = config.get(CONF_NAME)
    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]
    ecu_id = config[CONF_ECU_ID]
    system_id = config[CONF_SYSTEM_ID]

    sensor = ApsystemsSensor(sensor_name, username, password, ecu_id, system_id)
    async_add_entities([sensor])


class ApsystemsSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, sensor_name, username, password, ecu_id, system_id):
        """Initialize the sensor."""
        self._state = None
        self._name = sensor_name
        self._username = username
        self._password = password
        self._ecu_id = ecu_id
        self._system_id = system_id

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
        fetcher = APsystemsFetcher(self._username, self._password, self._ecu_id, self._system_id)
        data = fetcher.data()
        _LOGGER.debug(pprint.pformat(data))

        self._state = 23

    def find_start_time(self, now):
        """Return sunrise or start_time if given."""
        sunrise = get_astral_event_date(self.hass, SUN_EVENT_SUNRISE, now.date())
        return sunrise

    def find_stop_time(self, now):
        """Return sunset or stop_time if given."""
        sunset = get_astral_event_date(self.hass, SUN_EVENT_SUNSET, now.date())
        return sunset


class APsystemsFetcher:
    url_login = "https://apsystemsema.com/ema/loginEMA.action"
    #url_profile = "https://ema.api.apsystemsema.com:9223/aps-api-web/api/view/registration/user/getUserInfoWithSystemInfo"
    url_info = "https://apsystemsema.com/ema/ajax/getDownLoadReportApiAjax/getHourlyEnergyOnCurrentDayAjax"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0'}

    def __init__(self, username, password, ecu_id, system_id):
        self._username = username
        self._password = password
        self._ecu_id = ecu_id
        self._system_id = system_id
        self.today = datetime.fromisoformat(date.today().isoformat())

    def login(self):
        params = {'today': datetime.today().strftime("%Y-%m-%d+%H:%M:%S"),
                  'username':	self._username,
                  'password':	self._password}

        session = requests.session()
        session.mount('https://', HTTPAdapter())

        # should be call twice to correctly display
        session.request("POST", self.url_login, data=params, headers=self.headers)

        return session

    def data(self):
        session = self.login()

        params = {'queryDate': datetime.today().strftime("%Y%m%d"),
                  'ecuId':  self._ecu_id,
                  'userId':  self._system_id,
                  'systemId': self._system_id}

        result_data = session.request("POST", self.url_info, data=params, headers=self.headers)

        return result_data.json()