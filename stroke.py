import asyncio, websockets, json, logging, sys 
from buttplug import Client, WebsocketConnector, ProtocolSpec

class DeviceController:
    def __init__(self, intiface_central_ip="127.0.0.1", intiface_central_port="12345"):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.devices, self.client = self.loop.run_until_complete(self.setup(intiface_central_ip, intiface_central_port))
        self.current_tasks = []

    async def control_device(self, device, duration, intensity, oscillation=False, rotation_clockwise=None):
        """
        Function to control all device on duration, intensity, oscillation and rotation
        :param device: buttplug Device object
        :param duration: Duration of the command in ms
        :param intensity: Intensity of the command, ranging from 0 to 1
        :param actuator_type: Type of actuator. Possible values: "scalar", "linear", "rotatory"
        :param oscillation: True for infinite oscillation between 0.0 to "intensity".
        :param rotation_clockwise: For rotatory actuator, rotation direction. True for clockwise, False for anticlockwise.
        """
        try:
            original_intensity = intensity; inactive_state = 0
            if len(device.actuators) != 0:
                while True:
                    await device.actuators[0].command(intensity)
                    await asyncio.sleep(duration/1000)
                    # print(" actuators ..." + str(duration) + " intensity:" +  str(intensity))
                    if oscillation: intensity = original_intensity if intensity == inactive_state else inactive_state; 
                    else: break
                await device.actuators[0].command(0.0)
    
            if len(device.linear_actuators) != 0:
                inactive_state = 1
                while True:
                    await device.linear_actuators[0].command(duration, intensity)
                    await asyncio.sleep(duration/1100)
                    # print(" linear actuators ..." + str(duration) + " intensity:" +  str(intensity))
                    if oscillation: intensity = original_intensity if intensity == inactive_state else inactive_state; 
                    else: break
        
            if len(device.rotatory_actuators) != 0:
                while True:
                    await device.rotatory_actuators[0].command(intensity, rotation_clockwise)
                    await asyncio.sleep(duration/1000)
                    if oscillation: intensity = original_intensity if intensity == inactive_state else inactive_state; 
                    else: break
                await device.rotatory_actuators[0].command(0, rotation_clockwise)
        except Exception as e:
            logging.error(f"Exception in control_device: {e}")

    async def setup(self, intiface_central_ip, intiface_central_port):
        client = Client("Stroker Client", ProtocolSpec.v3)
        connector = WebsocketConnector(f"ws://{intiface_central_ip}:{intiface_central_port}", logger=client.logger)
        try: await client.connect(connector)
        except Exception as e: logging.error(f"Could not connect to server, exiting: {e}"); return None, None
        await client.start_scanning()
        await asyncio.sleep(10)
        await client.stop_scanning()
        devices = []
        if len(client.devices) != 0:
            for index, device_id in enumerate(client.devices.keys()):
                device = client.devices[device_id]
                logging.info(f"Found device {index}: {device}")
                devices.append(device)
        else:
            logging.error("No devices found.")
        return devices, client

    async def server(self, websocket, path):
        command = await websocket.recv()
        command = json.loads(command)
        logging.info(f"Number of devices: {len(self.devices)}")
        for task in self.current_tasks:
            task.cancel()
        self.current_tasks = []
        for device in self.devices:
            task = asyncio.create_task(self.control_device(device, command['duration'], command['intensity'], command['oscillation'], command.get('rotation_clockwise', None)))  # Create a new task
            self.current_tasks.append(task)
        await asyncio.gather(*self.current_tasks)


def main(router_ip="127.0.0.1", router_port=8769, intiface_central_ip="127.0.0.1", intiface_central_port="12345"):
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    controller = DeviceController(intiface_central_ip, intiface_central_port)
    start_server = websockets.serve(controller.server, router_ip, router_port)
    
    try: controller.loop.run_until_complete(start_server), controller.loop.run_forever()
    except KeyboardInterrupt: print("Exit Server"), [task.cancel() for task in asyncio.all_tasks(controller.loop)], controller.loop.run_until_complete(asyncio.gather(*asyncio.all_tasks(controller.loop), return_exceptions=True)), controller.loop.run_until_complete(controller.client.disconnect()), controller.loop.close()

if __name__ == "__main__":
    main()
