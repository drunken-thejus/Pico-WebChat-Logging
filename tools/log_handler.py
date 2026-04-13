# log_handler.py

import logging
import asyncio
from log_ws_manager import log_manager

class WebSocketLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(log_manager.broadcast(log_entry))
        except RuntimeError:
            pass  # ignore if no loop