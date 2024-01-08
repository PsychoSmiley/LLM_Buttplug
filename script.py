import gradio as gr
import torch, re, os
from transformers import LogitsProcessor
from modules.logging_colors import logger
from modules import chat, shared
from modules.text_generation import (
    decode,
    encode,
    generate_reply,
)

params = {
    "display_name": "Stroker",
    "is_tab": False,

    "enable_trigger_word": True,
    "trigger_word": "stroke(",
    "visible_input_modfier_function": True,
    "enable_input_modfier_function": True,
    "string_after_input_modfier_function": '", "context": "..."}',

    "duration": 1000,
    "intensity": 0.5,
    "actuator_type": "linear",

    "router_port": 8769,
    "router_ip": "127.0.0.1"
}

import asyncio, websockets, json
async def send_command(duration, intensity, actuator_type, rotation_clockwise=None):
    command = {
        "duration": duration,
        "intensity": intensity,
        "actuator_type": actuator_type,
        "rotation_clockwise": rotation_clockwise
    }
    async with websockets.connect(f'ws://{params["router_ip"]}:{params["router_port"]}') as websocket:
        await websocket.send(json.dumps(command))

def run_command(duration, intensity, actuator_type):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_command(duration, intensity, actuator_type))

def chat_input_modifier(text, visible_text, state):
    string_before = '{"input": "'
    string_after = params['string_after_input_modfier_function']
    
    if text.strip() and params['enable_input_modfier_function']:
        text = string_before + text + string_after
        if params['visible_input_modfier_function']:
            visible_text = string_before + visible_text + string_after
            
    return text, visible_text


from .stroke import main as stroke_main
import threading, socket

def setup():
    server_ip_address, server_port = params["router_ip"], params["router_port"]
    if params['enable_trigger_word'] and socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect_ex((server_ip_address, server_port)):
        logger.debug(f'Server stroke start in 10 second Scanning devices. Listen: {params["router_ip"]}:{params["router_port"]}')
        threading.Thread(target=stroke_main, args=(server_ip_address, server_port)).start()

def output_modifier(string, state, is_chat=False):
    global params

    duration = params["duration"]
    intensity = params["intensity"]
    actuator_type = params["actuator_type"]
    
    last_message_AI = string
    if params['enable_trigger_word'] and params['trigger_word'].lower() in last_message_AI.lower():
        trigger_index = last_message_AI.lower().index(params['trigger_word'].lower())
        open_parenthesis_index = last_message_AI.index('(', trigger_index)
        close_parenthesis_index = last_message_AI.index(')', open_parenthesis_index)
        substring = last_message_AI[open_parenthesis_index+1 : close_parenthesis_index]    
        try:
            intensity = max(0.0, min(float(substring), 1.0)) 
            logger.info(f"Intensity extracted from {params['trigger_word']} {intensity} ):: run_command: {duration}, {intensity}, {actuator_type}")
            run_command(duration, intensity, actuator_type)
        except Exception as e:
            logger.info(f"error string extraction: {e}")
        
    return string

def ui():
    global params

    with gr.Accordion("Stroker Settings"):
        with gr.Tab("Stroker Settings Client "):
            with gr.Row():
                with gr.Column(min_width=100):
                    checkbox_trigger_word = gr.Checkbox(label="Enable trigger_word", value=params["enable_trigger_word"])
                    textbox_trigger_word = gr.Textbox(label="Trigger word", value=params['trigger_word'], visible=params["enable_trigger_word"])
                with gr.Column(min_width=100):
                    checkbox_input_modfier_function = gr.Checkbox(label="Enable input_modfier_function", value=params["enable_input_modfier_function"])
                    textbox_input_modfier_word = gr.Textbox(label="End input_modfier string", value=params['string_after_input_modfier_function'], visible=params["enable_input_modfier_function"])
                    checkbox_visible_input_modfier_function = gr.Checkbox(label="Visible input modifier function", value=params["visible_input_modfier_function"])
                with gr.Column(min_width=100):
                    slider_duration = gr.Slider(minimum=0, maximum=5000, step=100, value=1000, label="Duration", info='Duration in ms.', interactive=True)
                    dropdown_actuator_type = gr.Dropdown(choices=["scalar", "linear", "rotatory"], value="linear", label="Actuator Type", interactive=True)
                with gr.Column(min_width=100):
                    router_port = gr.Number(value=params["router_port"], label="Router Port", info="The port on service will run.", precision=0)
                    router_ip = gr.Textbox(value=params["router_ip"], label="Router IP Address", info="The IP address on service will run.")

            # Event functions to update the params dictionary in the backend
            checkbox_trigger_word.change(lambda x: params.update({"enable_trigger_word": x}), checkbox_trigger_word, None)
            textbox_trigger_word.change(lambda x: params.update({"trigger_word": x}), textbox_trigger_word, None)
            checkbox_input_modfier_function.change(lambda x: params.update({"enable_input_modfier_function": x}), checkbox_input_modfier_function, None)
            textbox_input_modfier_word.change(lambda x: params.update({"string_after_input_modfier_function": x}), textbox_input_modfier_word, None)
            checkbox_visible_input_modfier_function.change(lambda x: params.update({"visible_input_modfier_function": x}), checkbox_visible_input_modfier_function, None)
            slider_duration.change(lambda x: params.update({"duration": x}), slider_duration, None)
            dropdown_actuator_type.change(lambda x: params.update({"actuator_type": x}), dropdown_actuator_type, None)
            router_port.change(lambda x: params.update({"router_port": x}), router_port, None)
            router_ip.change(lambda x: params.update({"router_ip": x}), router_ip, None)
