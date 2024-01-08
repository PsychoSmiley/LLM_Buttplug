import asyncio, websockets, json, logging, sys 
from buttplug import Client, WebsocketConnector, ProtocolSpec # import pip; pip.main(['install', 'buttplug-py'])

class DeviceController:
    def __init__(self, intiface_central_ip="127.0.0.1", intiface_central_port="12345"):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.device, self.client = self.loop.run_until_complete(self.setup(intiface_central_ip, intiface_central_port))

    async def control_device(self, device, duration, intensity, actuator_type, rotation_clockwise=None):
        """
        Function to control the device based on the actuator type, duration, intensity and rotation
        :param device: buttplug Device object
        :param duration: Duration of the command in ms
        :param intensity: Intensity of the command, ranging from 0 to 1
        :param actuator_type: Type of actuator. Possible values: "scalar", "linear", "rotatory"
        :param rotation_clockwise: For rotatory actuator, rotation direction. True for clockwise, False for anticlockwise.
        """
        if actuator_type == "scalar" and len(device.actuators) != 0:
            await device.actuators[0].command(intensity)
        elif actuator_type == "linear" and len(device.linear_actuators) != 0:
            await device.linear_actuators[0].command(duration, intensity)
        elif actuator_type == "rotatory" and len(device.rotatory_actuators) != 0:
            await device.rotatory_actuators[0].command(intensity, rotation_clockwise)

    async def setup(self, intiface_central_ip, intiface_central_port):
        client = Client("Stroker Client", ProtocolSpec.v3)
        connector = WebsocketConnector(f"ws://{intiface_central_ip}:{intiface_central_port}", logger=client.logger)
        try: await client.connect(connector)
        except Exception as e: logging.error(f"Could not connect to server, exiting: {e}"); return None, None
        await client.start_scanning()
        await asyncio.sleep(10)
        await client.stop_scanning()
        device = client.devices[0] if len(client.devices) != 0 else (logging.error("No devices found."), None)[1]
        return device, client

    async def server(self, websocket, path):
        command = await websocket.recv()
        command = json.loads(command)
        await self.control_device(self.device, command['duration'], command['intensity'], command['actuator_type'], command['rotation_clockwise'])

def main(router_ip="127.0.0.1", router_port=8769, intiface_central_ip="127.0.0.1", intiface_central_port="12345"):
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    controller = DeviceController(intiface_central_ip, intiface_central_port)
    start_server = websockets.serve(controller.server, router_ip, router_port)
    
    try: controller.loop.run_until_complete(start_server), controller.loop.run_forever()
    except KeyboardInterrupt: print("Exit"), [task.cancel() for task in asyncio.all_tasks(controller.loop)], controller.loop.run_until_complete(asyncio.gather(*asyncio.all_tasks(controller.loop), return_exceptions=True)), controller.loop.run_until_complete(controller.client.disconnect()), controller.loop.close()


if __name__ == "__main__":
    main()
