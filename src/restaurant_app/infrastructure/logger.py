import logging
import os
from logging.config import fileConfig
from os import path

__application_logger = "App"
LOG: logging.Logger = logging.getLogger(__application_logger)


def setup_logging(base_path):
    config_file = path.join(base_path, "logger.ini")
    if path.exists(config_file):
        print("LOG: will load logging configuration from: %s" % config_file)
        fileConfig(config_file)
        return

    # try to use the path defined in the file LOGGING_CONFIG_PATH
    config_file = os.getenv("LOGGING_CONFIG_PATH")
    if config_file and not config_file == "":
        print("LOG: logging configuration from LOGGING_CONFIG_PATH: %s" % config_file)
        fileConfig(config_file)
        return
