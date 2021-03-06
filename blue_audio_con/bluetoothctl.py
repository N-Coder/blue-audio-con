import re
import subprocess
import time
from contextlib import ContextDecorator

import pexpect


class BluetoothctlError(Exception):
    """This exception is raised, when bluetoothctl fails to start."""
    pass


class Bluetoothctl(ContextDecorator):
    """A wrapper for bluetoothctl utility."""

    def __enter__(self):
        out = subprocess.check_output("rfkill unblock bluetooth", shell=True)
        self.child = pexpect.spawnu("bluetoothctl", echo=False)
        return self

    def __exit__(self, *exc):
        self.child.close(force=True)
        return False

    def get_output(self, command, pause=0):
        """Run a command in bluetoothctl prompt, return output as a list of lines."""
        self.child.send(command + "\n")
        time.sleep(pause)
        start_failed = self.child.expect([(re.compile("\x1b\[0;94m\[.*\]\x1b\[0m# ")), pexpect.EOF], timeout=5)

        if start_failed:
            raise BluetoothctlError("Bluetoothctl failed after running " + command)

        return self.child.before.split("\r\n")

    def start_scan(self):
        """Start bluetooth scanning process."""
        return self.get_output("scan on")

    def stop_scan(self):
        """Stop bluetooth scanning process."""
        return self.get_output("scan off")

    def make_discoverable(self):
        """Make device discoverable."""
        return self.get_output("discoverable on")

    def parse_device_info(self, info_string):
        """Parse a string corresponding to a device."""
        device = {}
        block_list = ["[\x1b[0;", "removed"]
        string_valid = not any(keyword in info_string for keyword in block_list)

        if string_valid:
            try:
                device_position = info_string.index("Device")
            except ValueError:
                pass
            else:
                if device_position > -1:
                    attribute_list = info_string[device_position:].split(" ", 2)
                    device = {
                        "mac_address": attribute_list[1].strip(),
                        "name": attribute_list[2].strip()
                    }

        return device

    def get_available_devices(self):
        """Return a list of tuples of paired and discoverable devices."""
        out = self.get_output("devices")
        available_devices = []
        for line in out:
            device = self.parse_device_info(line)
            if device:
                available_devices.append(device)

        return available_devices

    def get_paired_devices(self):
        """Return a list of tuples of paired devices."""
        out = self.get_output("paired-devices")
        paired_devices = []
        for line in out:
            device = self.parse_device_info(line)
            if device:
                paired_devices.append(device)

        return paired_devices

    def get_discoverable_devices(self):
        """Filter paired devices out of available."""
        available = self.get_available_devices()
        paired = self.get_paired_devices()

        return [d for d in available if d not in paired]

    def get_device_info(self, mac_address):
        """Get device info by mac address."""
        return self.get_output("info " + mac_address)

    def pair(self, mac_address):
        """Try to pair with a device by mac address."""
        out = self.get_output("pair " + mac_address, 4)
        res = self.child.expect(["Pairing successful", "Failed to pair", pexpect.EOF, pexpect.TIMEOUT])
        return res == 0

    def remove(self, mac_address):
        """Remove paired device by mac address, return success of the operation."""
        out = self.get_output("remove " + mac_address, 3)
        res = self.child.expect(["Device has been removed", "not available", pexpect.EOF, pexpect.TIMEOUT])
        return res == 0

    def connect(self, mac_address):
        """Try to connect to a device by mac address."""
        out = self.get_output("connect " + mac_address, 2)
        res = self.child.expect(["Connection successful", "Failed to connect", pexpect.EOF, pexpect.TIMEOUT])
        return res == 0

    def disconnect(self, mac_address):
        """Try to disconnect to a device by mac address."""
        out = self.get_output("disconnect " + mac_address, 2)
        res = self.child.expect(["Successful disconnected", "Failed to disconnect", pexpect.EOF, pexpect.TIMEOUT])
        return res == 0
