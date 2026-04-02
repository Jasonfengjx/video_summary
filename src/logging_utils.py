import logging
import os
from logging.handlers import TimedRotatingFileHandler


def setup_logging(logs_dir: str, level: str = "INFO") -> None:
    os.makedirs(logs_dir, exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(logs_dir, "app.log"),
        when="D",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
