import logging
from contextlib import ContextDecorator

import gi

gi.require_version('Notify', '0.7')
from gi.repository import Notify
from gi.repository import GLib

STATUS_IN_PROGRESS = 0
STATUS_SUCCESS = 1
STATUS_FAILED = 2


class Notification(ContextDecorator):
    def __init__(self):
        self.notification = None
        self.logger = logging.getLogger()

    def __enter__(self):
        Notify.init('blue-audio-con')
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type:
            self.update("Failed: %s" % repr(exc_type), STATUS_FAILED)
        if self.notification:
            self.notification.set_hint("resident", GLib.Variant('b', False))
            self.notification.set_timeout(-1)  # NOTIFY_EXPIRES_DEFAULT
            self.notification.show()
        Notify.uninit()

        return False

    def update(self, text=None, status=STATUS_IN_PROGRESS):
        if text:
            if status == STATUS_FAILED:
                self.logger.error(text)
            else:
                self.logger.info(text)

        icon = {
            STATUS_IN_PROGRESS: "audio-volume-low",
            STATUS_SUCCESS: "audio-volume-high",
            STATUS_FAILED: "audio-volume-muted"
        }[status]
        if not self.notification:
            self.notification = Notify.Notification.new("Bluetooth Audio Device Assistant", text, icon)
        elif text:
            self.notification.update("Bluetooth Audio Device Assistant", text, icon)

        self.notification.set_urgency(0 if status == STATUS_IN_PROGRESS else 1)
        self.notification.set_hint("resident", GLib.Variant('b', True))
        self.notification.set_timeout(0)  # NOTIFY_EXPIRES_NEVER
        self.notification.show()
