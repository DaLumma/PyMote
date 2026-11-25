from typing import Literal

import requests

Playback = Literal[
    "play", "stop", "pause", "play_pause", "previous", "next",
    "fast_reverse_start", "fast_reverse_end", "fast_forward_start",
    "fast_forward_end"
]

class Yamaha:
    def __init__(self, ip):
        self.base_url = f"http://{ip}/YamahaExtendedControl/v1/"

    def _send(self, command):
        request = requests.get(self.base_url + command)
        query = request.json()
        request.close()
        return query

    def print_base_url(self):
        print(self.base_url)

    def toggle_power(self):
        self._send("main/setPower?power=toggle")

    def switch_input(self, source):
        self._send(f"main/setInput?input={source}")

    def control_playback(self, control):
        self._send(f"netusb/setPlayback?playback={control}")

    def control_volume(self, is_up=True, step=1):
        if is_up:
            self._send(f"main/setVolume?volume=up&step={step}")
        else:
            self._send(f"main/setVolume?volume=down&step={step}")

    def toggle_mute(self):
        new_state = "false" if self._send("main/getStatus")["mute"] else "true"
        self._send(f"main/setMute?enable={new_state}")
