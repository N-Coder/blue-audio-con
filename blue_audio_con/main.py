import logging.config
import time
from contextlib import ExitStack

from pulsectl import Pulse

from blue_audio_con.bluetoothctl import Bluetoothctl
from blue_audio_con.deviceui import show_window
from blue_audio_con.notification import Notification, STATUS_SUCCESS

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
        "handlers": ["syslog", "console"]
    },
    "disable_existing_loggers": False
})


def is_connected(info):
    return "\tConnected: yes" in info


def find_sink(mac, pulse):
    sinks = [sink for sink in pulse.sink_list()
             if sink.name.startswith("bluez_sink.%s" % mac.replace(":", "_"))]
    assert len(sinks) > 0
    return sinks[0]


def reset_card(pulse, card):
    for p in ["a2dp_sink", "off", "headset_head_unit", "off", "a2dp_sink"]:
        logger.debug("Set profile to %s", p)
        pulse.card_profile_set(card, p)
        time.sleep(0.1)


def find_card(pulse, mac):
    cards = [card for card in pulse.card_list()
             if card.name.startswith("bluez_card.%s" % mac.replace(":", "_"))]
    assert len(cards) > 0
    return cards[0]


def connect(bl, mac):
    for i in range(0, 20):
        logger.debug("Attempt %s of 20...", i)
        info = bl.get_device_info(mac)
        if is_connected(info):
            break
        if bl.connect(mac):
            time.sleep(1)
            break
        time.sleep(0.1)


def find_audio_devices(bl):
    devices = []
    for device in bl.get_paired_devices():
        info = bl.get_device_info(device["mac_address"])
        if any(profile in info for profile in
               ['\tUUID: Headset                   (00001108-0000-1000-8000-00805f9b34fb)',
                '\tUUID: Audio Sink                (0000110b-0000-1000-8000-00805f9b34fb)']):
            device["info"] = info
            device["available"] = any(value for value in info if value.startswith("\tRSSI:"))
            if is_connected(info):
                devices = [device]
                break
            else:
                devices.append(device)
    return devices


def bluetooth_main(notify):
    notify.update("Init bluetooth...")
    with ExitStack() as stack:
        bl = stack.enter_context(Bluetoothctl())
        logfile = open("/tmp/blue-audio-con.btctl.log", "w")
        bl.child.logfile = stack.enter_context(logfile)

        notify.update("Bluetooth ready, starting scan.")
        bl.start_scan()

        notify.update("Listing audio devices...")
        devices = find_audio_devices(bl)

        if len(devices) == 1:
            notify.update("Only found 1 device, connecting directly")
            mac = devices[0]["mac_address"]
        else:
            notify.update("Found %s devices, showing chooser" % len(devices))
            mac = show_window(devices)

        notify.update("Connecting to %s" % mac)
        connect(bl, mac)
        assert is_connected(bl.get_device_info(mac))
    return mac


def pulse_main(notify, mac):
    notify.update("Init pulse...")
    with Pulse('blue-audio-con') as pulse:
        notify.update("Pulse connected, looking for bluez card and sink")
        card = find_card(pulse, mac)
        sink = find_sink(mac, pulse)

        notify.update("Resetting profiles for %s" % card)
        reset_card(pulse, card)

        notify.update("Setting default sink to %s" % sink)
        pulse.sink_default_set(sink)

        for input in pulse.sink_input_list():
            notify.update("Moving input %s to bluez sink" % input)
            pulse.sink_input_move(input.index, sink.index)

        notify.update("Setting profile for %s to a2dp" % card)
        pulse.card_profile_set(card, "a2dp_sink")
        # TODO set gnome audio profile


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
