from fastapi.websockets import WebSocket
from typing import Dict
from tools.pico_ai import *

active_connections:Dict[str,WebSocket]={}
pico_connections:Dict[str,PicoAI]={}