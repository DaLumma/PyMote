import base64
import json
import ssl
from enum import StrEnum
from typing import Literal

import requests
from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect

Key = Literal[
    "KEY_POWER", "KEY_HOME", "KEY_MENU", "KEY_SOURCE", "KEY_EXIT", "KEY_RETURN",
    "KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT", "KEY_ENTER",
    "KEY_VOLUP", "KEY_VOLDOWN", "KEY_MUTE",
    "KEY_CHUP", "KEY_CHDOWN",
    "KEY_PLAY", "KEY_PAUSE", "KEY_STOP", "KEY_FF", "KEY_REWIND",
    "KEY_0", "KEY_1", "KEY_2", "KEY_3", "KEY_4",
    "KEY_5", "KEY_6", "KEY_7", "KEY_8", "KEY_9",
    "KEY_INFO", "KEY_GUIDE", "KEY_TOOLS",
]

class App(StrEnum):
    NETFLIX = "3201907018807"
    YOUTUBE = "111299001912"
    PRIME_VIDEO = "3201910019365"
    DISNEY_PLUS = "3201901017640"
    SPOTIFY = "3201606009684"

class TizenTV:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    def __init__(self, ip, remote_name="CouchRemote", token_file="tv_token.txt"):
        self.ip = ip
        self.remote_name = remote_name
        self.token_file = token_file
        self.name_b64 = base64.b64encode(remote_name.encode()).decode()
        self.url = f"wss://{self.ip}:8002/api/v2/channels/samsung.remote.control?name={self.name_b64}"
        self.ws = None

    def open_app(self, app_id: App | str):
        requests.post(f"http://{self.ip}:8001/api/v2/applications/{app_id}", timeout=5)

    def _load_token(self):
        try:
            with open(self.token_file) as f:
                return f.read().strip()
        except OSError:
            return None

    def _save_token(self, token):
        with open(self.token_file, "w") as f:
            f.write(token)
        print("Saved TV token")

    def connect(self):
        token = self._load_token()
        url = self.url + (f"&token={token}" if token else "")
        self.ws = connect(url, ssl=self.ctx)
        reply = json.loads(self.ws.recv(timeout=60))

        if reply.get("event") != "ms.channel.connect":
            print("Not allowed in")
            raise SystemExit

        new_token = reply.get("data", {}).get("token")
        if new_token and new_token != token:
            self._save_token(new_token)

    def close(self):
        self.ws.close()

    def send_key(self, key: Key):
        message = {
            "method": "ms.remote.control",
            "params": {
                "Cmd": "Click",
                "DataOfCmd": key,
                "Option": "false",
                "TypeOfRemote": "SendRemoteKey",
            },
        }
        self._send_json(message)

    def _send_json(self, data):
        if self.ws is None:
            self.connect()
        payload = json.dumps(data)
        try:
            self.ws.send(payload)
        except ConnectionClosed:
            print("connection lost, reconnecting...")
            self.ws.send(payload)
