import logging
import time

from pulsectl import Pulse

logger = logging.getLogger("pulse")


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
