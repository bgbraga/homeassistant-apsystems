[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs) [![apsystems](https://img.shields.io/github/v/release/bgbraga/homeassistant-apsystems.svg)](https://github.com/bgbraga/homeassistant-apsystems) ![Maintenance](https://img.shields.io/maintenance/yes/2021.svg)

# APsystems Sensor for Home Assistant
This component simplifies the integration of a APsystems inverter:
* creates up to individuals sensors for easy display or use in automations
* collects power (W) and energy (KWH) every 5 minutes
* extract data from apsystemsema.com web portal instead of hack the ECU connection
* supports any kind of ASsystems inverter or ECU
* pauses from sunset to sunrise to handle inverter logging going offline at night
* have a cache system to avoid individual sensors request the same data to apsystemsema.com

### URL's Utilised
The URL called is ``https://apsystemsema.com/ema/ajax/getReportApiAjax/getPowerOnCurrentDayAjax``
It is only called from sunset to sunrise and the sensor going offline at night

### Installation
Use [HACS](https://custom-components.github.io/hacs/) to point to this github URL:
https://github.com/bgbraga/homeassistant-apsystems

### Configuration
```yaml
# Minimal configuration.yaml entry:
sensor:
  - platform: apsystems
    username: apsystemsema_user
    password: !secret apsystems
    systemId: apsystemsema_system_id

