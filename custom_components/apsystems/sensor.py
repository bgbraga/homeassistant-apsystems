import logging
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.sun import get_astral_event_date
from homeassistant.util.dt import utcnow as dt_utcnow, as_local
import voluptuous as vol
import pprint
import requests
import asyncio
from requests.adapters import HTTPAdapter
from datetime import datetime, timedelta, date
import time

CONF_USERNAME = 'username'
CONF_PASSWORD = 'password'
CONF_SYSTEM_ID = 'systemId'
CONF_NAME = 'name'

SENSOR_ENERGY_TOTAL = 'energy_total'
SENSOR_ENERGY_LATEST = 'energy_latest'
SENSOR_POWER_MAX = 'power_max'
SENSOR_POWER_LATEST = 'power_latest'
SENSOR_TIME = 'time'

EXTRA_TIMESTAMP = 'timestamp'

from homeassistant.const import (
    CONF_NAME, SUN_EVENT_SUNRISE, SUN_EVENT_SUNSET, STATE_UNAVAILABLE, ENERGY_KILO_WATT_HOUR, POWER_WATT, TIME_MILLISECONDS
    )

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_SYSTEM_ID): cv.string,
    vol.Optional(CONF_NAME, default='APsystems'): cv.string
})

# Key: ['json_key', 'unit', 'icon']
SENSORS = {
    SENSOR_ENERGY_TOTAL:  ['total', ENERGY_KILO_WATT_HOUR, 'mdi:solar-power'],
    SENSOR_ENERGY_LATEST: ['energy', ENERGY_KILO_WATT_HOUR, 'mdi:solar-power'],
    SENSOR_POWER_MAX:     ['max', POWER_WATT, 'mdi:solar-power'],
    SENSOR_POWER_LATEST:  ['power', POWER_WATT, 'mdi:solar-power'],
    SENSOR_TIME:  ['time', TIME_MILLISECONDS, 'mdi:clock-outline']
}

SCAN_INTERVAL = timedelta(minutes=5)
_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    sensor_name = config.get(CONF_NAME)
    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]
    system_id = config[CONF_SYSTEM_ID]

    #data fetcher
    fetcher = APsystemsFetcher(hass, username, password, system_id)

    sensors = []
    for type in SENSORS:
        metadata = SENSORS[type]

        sensor = ApsystemsSensor(sensor_name, username, password, system_id, fetcher, metadata)
        sensors.append(sensor)

    async_add_entities(sensors)

class ApsystemsSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, sensor_name, username, password, system_id, fetcher, metadata):
        """Initialize the sensor."""
        self._state = None
        self._name = sensor_name
        self._username = username
        self._password = password
        self._system_id = system_id
        self._fetcher = fetcher
        self._metadata = metadata
        self._attributes = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def state_attributes(self):
        """Return the device state attributes."""
        return self._attributes

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._metadata[1]

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._metadata[2]

    @property
    def available(self, utc_now=None):
        if utc_now is None:
            utc_now = dt_utcnow()
        now = as_local(utc_now)

        start_time = self.find_start_time(now)
        stop_time = self.find_stop_time(now)

        _LOGGER.debug("!!! Start Time, Stop Time, Name: {}, {}, {}".format(as_local(start_time), as_local(stop_time), self._name))

        return True

    async def async_update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        ap_data = await self._fetcher.data()
        _LOGGER.debug(pprint.pformat(ap_data))

        # state is not available
        if ap_data is None:
            self._state = STATE_UNAVAILABLE
            return

        index = self._metadata[0]
        value = ap_data[index]
        if isinstance(value, list):
            value = value[-1]

        eleven_hours = 11 * 60 * 60 * 1000  # to move apsystems timestamp to UTC

        #get timestamp
        timestamp = ap_data[SENSOR_TIME][-1]

        if value == timestamp:  # current attribute is the timestamp, so fix it
            value = int(value) + eleven_hours
        timestamp = int(timestamp) + eleven_hours

        self._attributes[EXTRA_TIMESTAMP] = timestamp

        _LOGGER.debug(value)
        self._state = value

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
    url_data = "https://apsystemsema.com/ema/ajax/getReportApiAjax/getPowerOnCurrentDayAjax"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0'}
    cache = None
    running = False

    def __init__(self, hass, username, password, system_id):
        self._hass = hass
        self._username = username
        self._password = password
        self._system_id = system_id
        self._today = datetime.fromisoformat(date.today().isoformat())

    async def login(self):
        params = {'today': datetime.today().strftime("%Y-%m-%d+%H:%M:%S"),
                  'username':	self._username,
                  'password':	self._password}

        session = requests.session()
        session.mount('https://', HTTPAdapter())

        result_login = await self._hass.async_add_executor_job(
            session.request, "POST", self.url_login, data=params, headers=self.headers
        )

        _LOGGER.debug("status code login: " + str(result_login.status_code))

        return session

    async def run(self):
        self.running = True
        try:
            session = await self.login()

            params = {'queryDate': datetime.today().strftime("%Y%m%d"),
                      'selectedValue': '216000045871',
                      'systemId': self._system_id}

            agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            _LOGGER.debug('vai rodar: ' + agora)
            result_data = session.request("POST", self.url_data, data=params, headers=self.headers)

            _LOGGER.debug("status code data: " + str(result_data.status_code))
            _LOGGER.debug(result_data.json())

            if result_data.status_code == 204:
                self.cache = None
            else:
                self.cache = result_data.json()
        finally:
            self.running = False

    async def data(self):
        while self.running is True:
            await asyncio.sleep(1)

        if self.cache is None:
            self.run()

        # continue None after run(), there is no data for this day
        if self.cache is None:
            return self.cache

        # rules to check cache
        eleven_hours = 11 * 60 * 60 * 1000
        timestamp_event = int(self.cache['time'][-1]) + eleven_hours  # apsystems have 8h delayed in timestamp from UTC
        timestamp_now = int(round(time.time() * 1000))
        cache_time = 6 * 60 * 1000  # 6 minutes

        if timestamp_now - timestamp_event > cache_time:
            self.run()

        return self.cache
