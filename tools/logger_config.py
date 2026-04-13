import logging
from pythonjsonlogger import jsonlogger

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