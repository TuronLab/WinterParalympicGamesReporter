import logging
import os


class ColorFormatter(logging.Formatter):
    # ANSI color codes
    COLORS = {
        logging.INFO:    "\033[0m",          # white / default
        logging.WARNING: "\033[33m",         # yellow
        logging.ERROR:   "\033[31m",         # red
        logging.CRITICAL:"\033[1;31m",       # bright red
    }
    RESET = "\033[0m"

    def format(self, record):
        # Pick color based on level
        color = self.COLORS.get(record.levelno, self.RESET)
        message = super().format(record)
        return f"{color}{message}{self.RESET}"

def config_logger(log_file, used_by='MONITOR'):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger(used_by.lower() + "_logger")
    logger.setLevel(logging.DEBUG)

    fmt = f'%(asctime)s - [{used_by}] - %(levelname)s - %(message)s'

    # File handler (no colors)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(fmt))

    # Console handler (with colors)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColorFormatter(fmt))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # STOP log propagation to root logger
    logger.propagate = False

    logger.info("Logger initialized for %s, logs will be stored into %s",
                used_by, os.path.dirname(log_file))
    return logger

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.environ.get("LOG_PATH",  os.path.join(project_path, ".logs"))
REPORTER_LOGGER = config_logger(os.path.join(LOG_PATH, "merlin.log"), 'REPORTER_LOGGER')

COUNTRY_REGION_MAP = {
    "ITA": "it-it",
    "UKR": "uk-ua",
    "USA": "en-us",
    "GBR": "en-gb",
    "CHN": "zh-cn",
    "FRA": "fr-fr",
    "MGL": "mn-mn",
    "CZE": "cs-cz",
    "KAZ": "ru-kz",
    "RUS": "ru-ru",
    "BRA": "pt-br",
    "BLR": "ru-by",
    "JPN": "ja-jp",
    "GEO": "ka-ge",
    "ESA": "es-sv",
    "AUS": "en-au",
    "CAN": "en-ca",
    "GER": "de-de",
    "KOR": "ko-kr",
    "NOR": "no-no",
    "FIN": "fi-fi",
    "POL": "pl-pl",
    "SUI": "de-ch",
    "SWE": "sv-se",
    "SVK": "sk-sk",
    "ARG": "es-ar",
    "AUT": "de-at",
    "ESP": "es-es",
    "WORLD": "wt-wt",
}
