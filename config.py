from pathlib import Path

from sanic_envconfig import EnvConfig
from urlobject import URLObject


class Config(EnvConfig):
    DEBUG: bool = False
    PORT: int = 8000
    UPSTREAM_CRAN_SERVER_URL: URLObject = URLObject("https://cloud.r-project.org/")
    LOG_LEVEL: str = "INFO"
    BINARY_OUTPUT_PATH: Path = Path('/tmp/bin/')


def set_log_level(log_config):
    for logger in log_config.get("loggers", {}).values():
        logger["level"] = Config().LOG_LEVEL


def set_log_format(log_config):
    log_config["formatters"]["generic"][
        "format"
    ] = "%(asctime)s [%(process)d] [%(levelname)s] [%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"


def configure_logging(log_config):
    set_log_format(log_config)
    set_log_level(log_config)
