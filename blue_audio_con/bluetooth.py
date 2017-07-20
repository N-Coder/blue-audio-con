import logging
import time
from contextlib import ExitStack

from blue_audio_con.bluetoothctl import Bluetoothctl
from blue_audio_con.deviceui import show_chooser

logger = logging.getLogger("bluetooth")


def is_connected(info):
    return "\tConnected: yes" in info


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

        try:
            notify.update("Bluetooth ready, starting scan.")
            bl.start_scan()

            notify.update("Listing audio devices...")
            devices = find_audio_devices(bl)

            if len(devices) == 1:
                notify.update("Only found 1 device, connecting directly")
                mac = devices[0]["mac_address"]
            else:
                notify.update("Found %s devices, showing chooser" % len(devices))
                mac = show_chooser(devices)

            notify.update("Connecting to %s" % mac)
            connect(bl, mac)
            assert is_connected(bl.get_device_info(mac))
        finally:
            bl.stop_scan()
    return mac
