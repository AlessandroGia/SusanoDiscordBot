"""
This module configures the logging and loads environment variables for the Discord bot.

Functions:
    setup_logging(): Configures logging to use a TimedRotatingFileHandler.

Environment Variables:
    DISCORD_TOKEN: The token for the Discord bot.
    LAVA_HOST: The host for the LavaLink server.
    LAVA_PORT: The port for the LavaLink server.
    LAVA_PASSWORD: The password for the LavaLink server.
"""

from datetime import datetime
import logging
import os

from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv


load_dotenv()

discord_token = os.getenv('DISCORD_TOKEN')

lava_host = os.getenv('LAVA_HOST')
lava_port = os.getenv('LAVA_PORT')
lava_password = os.getenv('LAVA_PASSWORD')


def setup_logging():
    """
    Configures logging to use a TimedRotatingFileHandler.

    Creates a log directory if it does not exist, sets up a log file with a
    timestamp, and configures the logger to use a TimedRotatingFileHandler
    that rotates logs at midnight and keeps backups for 30 days.
    """
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, f'{datetime.now().strftime("%Y-%m-%d")}.log')

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=30)
    handler.suffix = "%Y-%m-%d"
    handler.extMatch = r"^\d{4}-\d{2}-\d{2}$"

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
