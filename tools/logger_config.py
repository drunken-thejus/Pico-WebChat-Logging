import logging
from pythonjsonlogger import jsonlogger
from logtail import LogtailHandler
import os
def setup_logger():
    logger = logging.getLogger()
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logger.setLevel(logging.INFO)

    # remove old handlers (important)
    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.StreamHandler()

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logtail_token=os.getenv("LOGTAIL_TOKEN")
    if logtail_token:
        logtail_handler = LogtailHandler(source_token=logtail_token)
        logtail_handler.setFormatter(formatter)
        logger.addHandler(logtail_handler)