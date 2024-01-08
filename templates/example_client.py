import asyncio, websockets, json, argparse

async def send_command(duration, intensity, oscillation=False, rotation_clockwise=None):
    command = {
        "duration": duration,
        "intensity": intensity,
        "oscillation": oscillation,
        "rotation_clockwise": rotation_clockwise
    }
    async with websockets.connect('ws://127.0.0.1:8769') as websocket:
        await websocket.send(json.dumps(command))

# Set up argument parsing eg. python example_client.py 100 0.5 True
parser = argparse.ArgumentParser(description='Send a command to the stroker device.')
parser.add_argument('duration', type=int, help='Duration of the command in ms')
parser.add_argument('intensity', type=float, help='Intensity of the command, ranging from 0 to 1')
parser.add_argument('oscillation', type=lambda x: (str(x).lower() == 'true'), nargs='?', default=False, help='Optional. If set to True, the device will oscillate.')
args = parser.parse_args()

# Run the client with the arguments
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(send_command(args.duration, args.intensity, args.oscillation))
