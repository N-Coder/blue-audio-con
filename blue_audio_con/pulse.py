import json
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


def set_gnome_sink(sink):
    """
    This function is likely to be my most dirty hack.
    Somehow telling PulseAudio which sink is the default one is not enough for GNOME to accept it as the new default sink.
    So we have to tell GNOME, or more precisely the gnome-volume-control library, which sink is the new default one explicitly.
    Because this library is not publicly available via GObject introspection, we have to use DBUS to inject JavaScript
    code into GNOME Shell, which has access to GVC.

    https://github.com/anduchs/audio-output-switcher/blob/master/extension.js
    https://github.com/GNOME/gnome-shell/blob/master/js/ui/status/volume.js
    https://github.com/GNOME/libgnome-volume-control/blob/master/gvc-mixer-control.h
    """
    import dbus
    bus = dbus.SessionBus()
    proxy = bus.get_object('org.gnome.Shell', '/org/gnome/Shell')

    status, result = proxy.Eval(
        # language=JavaScript
        """
    const Main = imports.ui.main;
    let control = Main.panel.statusArea.aggregateMenu._volume._control;
    let sinklist = control.get_sinks();
    let result = {};
    for (let i=0; i < sinklist.length; i++) {
        let sink = sinklist[i];
        let name = sink.get_name();
        result[i] = {
            "str": sink.toString(),
            "name": name,
            "desc": sink.get_description()
        };
        if (name == "%s") {
            control.set_default_sink(sink);
            result["default"] = name; 
        }
    }
    result;
    """ % sink, dbus_interface='org.gnome.Shell')
    result = json.loads(result)
    assert status == True
    assert result["default"] == sink
    return status, result


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

        # for input in pulse.sink_input_list():
        #     notify.update("Moving input %s to bluez sink" % input)
        #     pulse.sink_input_move(input.index, sink.index)

        notify.update("Setting GNOME sink to %s" % sink.name)
        set_gnome_sink(sink.name)

        notify.update("Setting profile for %s to a2dp" % card)
        pulse.card_profile_set(card, "a2dp_sink")
