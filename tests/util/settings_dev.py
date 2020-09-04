# app imports
from .settings_test import *

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": "tests.util.callback_show_debug_toolbar",
}

INSTALLED_APPS += [
    "debug_toolbar",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "dev_f": {
            "format": "[%(levelname)s] %(name)s:%(lineno)d:%(funcName)s \n\t %(message)s",
        },
    },
    "handlers": {"def_h": {"class": "logging.StreamHandler", "formatter": "dev_f",},},
    "loggers": {
        "stockings": {"handlers": ["def_h"], "level": "DEBUG", "propagate": False,}
    },
}
