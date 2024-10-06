import logging

CONSOLE_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
FILE_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class ColoredFormatter(logging.Formatter):
    GREY = "\x1b[38;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BLUE = "\x1b[34;20m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"
    FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
    FORMATTERS = {
        logging.DEBUG: logging.Formatter(BLUE + FORMAT + RESET, DATE_FORMAT),
        logging.INFO: logging.Formatter(GREY + FORMAT + RESET, DATE_FORMAT),
        logging.WARNING: logging.Formatter(YELLOW + FORMAT + RESET, DATE_FORMAT),
        logging.ERROR: logging.Formatter(RED + FORMAT + RESET, DATE_FORMAT),
        logging.CRITICAL: logging.Formatter(BOLD_RED + FORMAT + RESET, DATE_FORMAT),
    }
    DEFAULT_FORMATTER = logging.Formatter()

    @classmethod
    def format(cls, record):
        return cls.FORMATTERS.get(record.levelno, CONSOLE_FORMAT).format(record)


def getLogger(name: str):
    return logging.getLogger(name)


def init():
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(ColoredFormatter)  # type: ignore
    logging.basicConfig(level=logging.DEBUG, handlers=[consoleHandler])


def shutdown():
    logging.shutdown()
