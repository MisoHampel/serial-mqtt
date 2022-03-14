import hassapi as hass
import serial
import asyncio
import queue
import mqttapi as mqtt

commands = queue.Queue()


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
        self.listen_event(
            self.mqtt_init_callback,
            event="MQTT_MESSAGE",
            topic=self.args["init_topic"],
            namespace="mqtt",
        )

        for init_command in self.args["init_commands"]:
            commands.put(str(init_command))

        await self.connect_serial()
        await self.run_in(self.serial_read_loop, 2)

    # -------------------------------------------------------

    async def serial_read_loop(self, kwargs):
        # do some async stuff
        state_topic = self.args["state_topic"]
        while True:
            await asyncio.sleep(0.1)  # Time to yield in seconds. Use a shorter time if needed, i.e. 0.1.
            if not Context.serial_port == None and Context.serial_port.isOpen():
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
                if Context.serial_port != None:
                    Context.serial_port.close()
                    self.debug("Error - serial closed ")
                self.connect_serial()

    # ----------------------------------------------------
    async def connect_serial(self):
        connected = False
        while not connected:
            try:
                if Context.serial_port == None:
                    self.debug("Trying to open serial ... ")
                    Context.serial_port = serial.Serial(
                        port=self.args["serial_port"],  # /dev/ttyUSB0
                        baudrate=9600,  # 9600 bauds
                        bytesize=serial.EIGHTBITS,  # 7bits
                        parity=serial.PARITY_NONE,  # even parity
                        stopbits=serial.STOPBITS_ONE,  # 1 stop bit
                        xonxoff=False,  # no flow control
                        timeout=1,
                    )
                    self.debug("Serial is opened: " + Context.serial_port.name)
                    connected = True
                    continue
                elif Context.serial_port.isOpen():
                    connected = True
                    continue
                else:
                    self.debug("Error - serial closed ")
                    Context.serial_port.close()
                    Context.serial_port = None
                    connected = False
            except Exception as e:
                self.debug("Open serial ERROR " + str(e))
                connected = False
            if not connected:
                await asyncio.sleep(2)

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
        
    def mqtt_init_callback(self, event, event_data, kwargs):
        self.debug("MQTT-mqtt_init_callback")
        for init_command in self.args["init_commands"]:
            commands.put(str(init_command))

    # ----------------------------------------------------
    def debug(self, text):
        if self.args["DEBUG"] == 1:
            self.log(text)
