import logging.config
import time

from blue_audio_con.bluetooth import bluetooth_main
from blue_audio_con.notification import Notification, STATUS_SUCCESS
from blue_audio_con.pulse import pulse_main

logger = logging.getLogger()
logging.config.dictConfig({
    "version": 1,
    "formatters": {
        "simple": {'format': "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
        "syslog": {'format': "blue_audio_con-%(name)s: %(message)s"}
    },
    "handlers": {
        "syslog": {
            "class": "logging.handlers.SysLogHandler",
            "level": "DEBUG",
            "address": "/dev/log",
            "formatter": "syslog",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "DEBUG",
            "stream": "ext://sys.stdout",
        }
    },
    "root": {
        "level": "DEBUG",
        "handlers": [
            "syslog",
            # "console"
        ]
    },
    "disable_existing_loggers": False
})


def main():
    try:
        with Notification() as notify:
            mac = bluetooth_main(notify)
            time.sleep(2)
            pulse_main(notify, mac)
            notify.update("Done", status=STATUS_SUCCESS)
    except:
        logger.error("Connecting to bluetooth audio device failed!", exc_info=True)


if __name__ == "__main__":
    main()
