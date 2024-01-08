import asyncio, websockets, json, argparse

async def send_command(duration, intensity, actuator_type, rotation_clockwise=None):
    command = {
        "duration": duration,
        "intensity": intensity,
        "actuator_type": actuator_type,
        "rotation_clockwise": rotation_clockwise
    }
    async with websockets.connect('ws://127.0.0.1:8769') as websocket:
        await websocket.send(json.dumps(command))

# Set up argument parsing eg. python example_client.py 100 0.5 linear
parser = argparse.ArgumentParser(description='Send a command to the stroker device.')
parser.add_argument('duration', type=int, help='Duration of the command in ms')
parser.add_argument('intensity', type=float, help='Intensity of the command, ranging from 0 to 1')
parser.add_argument('actuator_type', type=str, help='Type of actuator. Possible values: "scalar", "linear", "rotatory"')
args = parser.parse_args()

# Run the client with the arguments
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(send_command(args.duration, args.intensity, args.actuator_type))
