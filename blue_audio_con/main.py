import time

from pulsectl import Pulse

from blue_audio_con.bluetoothctl import Bluetoothctl
from blue_audio_con.deviceui import show_message, show_window


def is_connected(info):
    return "\tConnected: yes" in info


def find_sink(mac, pulse):
    sinks = [sink for sink in pulse.sink_list()
             if sink.name.startswith("bluez_sink.%s" % mac.replace(":", "_"))]
    assert len(sinks) > 0
    return sinks[0]


def reset_card(pulse, card):
    for p in ["a2dp_sink", "off", "headset_head_unit", "off", "a2dp_sink"]:
        print("Set profile to %s" % p)
        pulse.card_profile_set(card, p)
        time.sleep(0.1)


def find_card(pulse, mac):
    cards = [card for card in pulse.card_list()
             if card.name.startswith("bluez_card.%s" % mac.replace(":", "_"))]
    assert len(cards) > 0
    return cards[0]


def connect(bl, mac):
    for i in range(0, 20):
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


# TODO show progress, failure, success notifications on-screen
# TODO set gnome audio profile
# TODO improve device list: show available devices, update, icons

def main():
    print("Init bluetooth...")
    with Bluetoothctl() as bl:
        print("Bluetooth ready, starting scan.")
        bl.start_scan()

        print("Listing audio devices...")
        devices = find_audio_devices(bl)

        if len(devices) == 1:
            print("Only found 1 device, connecting directly")
            mac = devices[0]["mac_address"]
        else:
            print("Found %s devices, showing chooser" % len(devices))
            mac = show_window(devices)

        print("Connecting to %s" % mac)
        connect(bl, mac)
        assert is_connected(bl.get_device_info(mac))

    time.sleep(2)
    print("Init pulse...")
    with Pulse('blue-audio-con') as pulse:
        print("Pulse connected, looking for bluez card and sink")
        card = find_card(pulse, mac)
        sink = find_sink(mac, pulse)

        print("Resetting profiles for %s" % card)
        reset_card(pulse, card)

        print("Setting default sink to %s" % sink)
        pulse.sink_default_set(sink)

        for input in pulse.sink_input_list():
            print("Moving input %s to bluez sink" % input)
            pulse.sink_input_move(input.index, sink.index)

        print("Setting profile for %s to a2dp" % card)
        pulse.card_profile_set(card, "a2dp_sink")

    print("Done")
    show_message("Done")


if __name__ == "__main__":
    main()
