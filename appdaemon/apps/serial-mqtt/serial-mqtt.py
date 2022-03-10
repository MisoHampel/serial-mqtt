import hassapi as hass
import serial
import asyncio
import queue
import mqttapi as mqtt

commands = queue.LifoQueue()


class Context:
    serial_port = None


class SerialMqtt(mqtt.Mqtt, hass.Hass):
    async def initialize(self):
        self.debug("Hello from AppDaemon serial " + str(Context.serial_port))

        command_topic = self.args["command_topic"]

        self.debug("command topic:" + command_topic)
        self.listen_event(
            self.mqtt_callback,
            event="MQTT_MESSAGE",
            topic=command_topic,
            namespace="mqtt",
        )

        try:
            if Context.serial_port == None:
                self.debug("MQTT: -> open serial ... ")
                Context.serial_port = serial.Serial(
                    port="/dev/serial/by-id/usb-1a86_USB2.0-Ser_-if00-port0",  # /dev/ttyUSB0
                    baudrate=9600,  # 9600 bauds
                    bytesize=serial.EIGHTBITS,  # 7bits
                    parity=serial.PARITY_NONE,  # even parity
                    stopbits=serial.STOPBITS_ONE,  # 1 stop bit
                    xonxoff=False,  # no flow control
                    timeout=1,
                )

            self.debug("Serial is opened: " + Context.serial_port.name)
            await self.run_in(self.serial_read_loop, 2)
        except Exception as e:
            self.debug("Open serial ERROR " + str(e))

    # -------------------------------------------------------

    async def serial_read_loop(self, kwargs):
        # do some async stuff
        state_topic = self.args["state_topic"]
        while True:
            await asyncio.sleep(0.2)  # Time to yield in seconds. Use a shorter time if needed, i.e. 0.1.
            if Context.serial_port != None:
                if Context.serial_port.isOpen():
                    if not commands.empty():
                        command = commands.get()
                        self.debug("Sending command to realy board: " + command)
                        Context.serial_port.write(bytes(command, "ascii"))
                    try:
                        # read
                        doc = Context.serial_port.readline()
                        if len(doc) > 2:
                            received = str(doc.decode("ascii")).strip()
                            self.debug("Serial answer " + received)
                            self.mqtt_publish(state_topic, received, retain=True)
                    except Exception as e:
                        self.debug("Error : try to parse an incomplete message")
                        pass
                #   Context.serial_port.flush()
                else:
                    self.debug("Error - serial closed ")

    # ----------------------------------------------------
    def terminate(self):
        self.debug("terminate enter")

        if Context.serial_port != None:
            Context.serial_port.close()
            self.debug("Error - serial closed ")

        self.debug("terminate exit")

    # ----------------------------------------------------
    def mqtt_callback(self, event, event_data, kwargs):
        self.debug("MQTT-mqtt_callback")

        topic = str(event_data.get("topic"))
        payload = str(event_data.get("payload"))

        self.debug("MQTT: topic " + topic + ", payload (command) " + payload)
        commands.put(payload)

    # ----------------------------------------------------
    def debug(self, text):
        if self.args["DEBUG"] == 1:
            self.log(text)
