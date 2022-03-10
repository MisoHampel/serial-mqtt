# serial-mqtt
## Home assistant - AppDaemon 4 app

This is an AppDaemon converter between serial and mqtt

## Installation
1. This requires AppDeamon installed and configured (follow the documentation on their web site).
2. Add mqtt config to `/config/appdaemon/appdaemon.yaml`
   ```yaml
    appdaemon:
        plugins:
            MQTT:
                type: mqtt
                namespace: mqtt
                client_host: mqtt-broker-addr
                client_id: appdaemon
                user_name: mqtt-username
                client_password: mqtt-password
                event_name: MQTT_MESSAGE
   ```
3. Make sure that `pyserial` is incuded in the `python_packages` option
4. Copy the content of the appdaemon directory from this repository to your home assistant 
`/config/appdaemon` folder
4. Add configuration to your Home Assistant's `/config/appdaemon/apps/apps.yaml`

## Configuration
This is the configuration that goes into `/config/appdaemon/apps/apps.yaml`

### Example
```yaml
serial-mqtt:
  module: serial-mqtt
  class: SerialMqtt
  DEBUG: 1
  state_topic: "serial-mqtt/state"
  command_topic: "serial-mqtt/command"
```

### Parameters
|Attribute |Required|Description
|:----------|----------|------------
| `module` | Yes | Always `rs232-relay-mqtt`
| `class` | Yes | Always `Rs232RelayMqtt`
| `DEBUG` | Yes | Flag that allow to log debug messages
| `state_topic` | Yes | State topic where answer from serial is send in payload
| `command_topic` | Yes | Command toppic where app is listening, payload is send to serial device

## MQTT sensor definition
```yaml
switch:
  - platform: mqtt
    name: "Relay 1"
    state_topic: "serial-mqtt/state"
    command_topic: "serial-mqtt/command"
    payload_on: "AT+O1"
    payload_off: "AT+C1"
    state_on: "Open1"
    state_off: "Close1"
```
## How it works
Everything what is send to `command_topic` is send to `serial device` and everything what is received from serial (filtered to line with 2 and more chars)is send to `state_topic` in `payload`