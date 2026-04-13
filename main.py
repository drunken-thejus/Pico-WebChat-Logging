from fastapi.staticfiles import StaticFiles
from routers.websockets import router as socket_router
from routers.api import router as api_router
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from supermiddleware import supermiddleware

import os

from tools.logger_config import setup_logger

setup_logger()  

app = FastAPI()
app.add_middleware(BaseHTTPMiddleware,supermiddleware)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(api_router)
app.include_router(socket_router)
