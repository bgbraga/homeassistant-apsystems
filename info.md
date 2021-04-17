[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs) [![apsystems](https://img.shields.io/github/v/release/bgbraga/homeassistant-apsystems.svg)](https://github.com/bgbraga/homeassistant-apsystems) ![Maintenance](https://img.shields.io/maintenance/yes/2021.svg)

### Features:
This component simplifies the integration of a APsystems inverter:
* creates up to individuals sensors for easy display or use in automations
* extract data from apsystemsema.com web portal instead of hack the ECU connection
* supports any kind of ASsystems inverter or ECU
* pauses from sunset to sunrise to handle inverter logging going offline at night

### Minimal Configuration
```
sensor:
- platform: apsystems
    ip_address: LOCAL_IP_FOR_FRONIUS
```
