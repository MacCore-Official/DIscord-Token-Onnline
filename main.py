import json
import random
import time
import os
import ssl
import threading
from enum import Enum, IntEnum
from typing import Dict, List, Optional, Union

import websocket
import requests
from colorama import Fore, Style, init

init(autoreset=True)

# --- CONFIGURATION ---
MY_USER_ID = "1269145029943758899"
active_workers = []

class Status(Enum):
    ONLINE = "online"
    DND = "dnd"
    IDLE = "idle"
    INVISIBLE = "invisible"

class Activity(Enum):
    GAME = 0
    STREAMING = 1
    LISTENING = 2
    WATCHING = 3
    CUSTOM = 4  
    COMPETING = 5

class OPCodes(IntEnum):
    Dispatch = 0
    Heartbeat = 1
    Identify = 2
    PresenceUpdate = 3
    Hello = 10
    HeartbeatACK = 11

class PresenceManager:
    """ Manages the data structure for Discord Presence Updates """
    def __init__(self, status: Status, text: str):
        self.status = status
        self.text = text

    def get_payload(self):
        return {
            "op": OPCodes.PresenceUpdate.value,
            "d": {
                "since": 0,
                "activities": [{
                    "type": Activity.CUSTOM.value,
                    "name": "Custom Status",
                    "state": self.text,
                    "id": "custom"
                }],
                "status": self.status.value,
                "afk": False
            }
        }

class DiscordWorker:
    """ Professional WebSocket Handler for Discord Gateway """
    def __init__(self, token: str):
        self.token = token
        self.ws = None
        self.heartbeat_interval = None
        self.username = "Unknown"

    def plog(self, symbol, text, extra=""):
        print(f"{Fore.CYAN}[{symbol}] {Fore.WHITE}{text.ljust(20)} | {Fore.MAGENTA}{self.username.ljust(15)} {Fore.BLUE}{extra}")

    def on_message(self, ws, message):
        data = json.loads(message)
        
        # Handle Hello (Heartbeat setup)
        if data.get("op") == OPCodes.Hello.value:
            self.heartbeat_interval = data["d"]["heartbeat_interval"] / 1000
            threading.Thread(target=self.heartbeat_loop, daemon=True).start()
            self.identify()

        # Handle Dispatch Events
        if data.get("op") == OPCodes.Dispatch.value:
            event_type = data.get("t")
            
            if event_type == "READY":
                self.username = data["d"]["user"]["username"]
                self.plog("🔑", "AUTHENTICATED", "READY")
                self.update_presence("rbxrise.com")

            if event_type == "MESSAGE_CREATE":
                msg = data["d"]
                content = msg.get("content", "")
                author_id = msg.get("author", {}).get("id")

                # MASTER COMMAND LOGIC
                if author_id == MY_USER_ID and content.startswith(".change "):
                    new_text = content.replace(".change ", "").strip()
                    print(f"\n{Fore.YELLOW}🚀 MASTER COMMAND: {new_text}")
                    for worker in active_workers:
                        worker.update_presence(new_text)

    def identify(self):
        payload = {
            "op": OPCodes.Identify.value,
            "d": {
                "token": self.token,
                "properties": {
                    "$os": "android",
                    "$browser": "Discord Android",
                    "$device": "Discord Android"
                },
                "presence": PresenceManager(Status.ONLINE, "rbxrise.com").get_payload()["d"]
            }
        }
        self.ws.send(json.dumps(payload))

    def update_presence(self, text: str):
        manager = PresenceManager(Status.ONLINE, text)
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps(manager.get_payload()))
            self.plog("✨", "STATUS UPDATED", text)

    def heartbeat_loop(self):
        while self.ws and self.ws.sock and self.ws.sock.connected:
            time.sleep(self.heartbeat_interval)
            self.ws.send(json.dumps({"op": OPCodes.Heartbeat.value, "d": None}))

    def run(self):
        self.ws = websocket.WebSocketApp(
            "wss://gateway.discord.gg/?v=9&encoding=json",
            on_message=self.on_message
        )
        self.ws.run_forever(ping_interval=20, sslopt={"cert_reqs": ssl.CERT_NONE})

def intro(count):
    print(Fore.GREEN + f"\n[!] Initializing Onliner... Total Tokens: {count}")
    print(Fore.RED + """
 ██████╗ ██╗ ██████╗ ██████╗ ██╗   ██╗ ██╗███████╗
 ██╔══██╗██║██╔════╝ ██╔════╝╚██╗ ██╔╝██╔╝██╔════╝
 ██████╔╝██║██║  ███╗██║  ███╗╚████╔╝ ╚═╝ ███████╗
 ██╔═══╝ ██║██║   ██║██║   ██║ ╚██╔╝      ╚════██║
 ██║     ██║╚██████╔╝╚██████╔╝  ██║       ███████║
 ╚═╝     ╚═╝ ╚═════╝  ╚═════╝   ╚═╝       ╚══════╝
    """ + Fore.CYAN + "Created By PiggyAwesome | MASTER MODE ACTIVE\n")

if __name__ == "__main__":
    token_list = os.getenv("DISCORDTOKENS", "").split(",")
    valid_tokens = [t.strip() for t in token_list if t.strip()]
    
    intro(len(valid_tokens))

    for token in valid_tokens:
        worker = DiscordWorker(token)
        active_workers.append(worker)
        threading.Thread(target=worker.run, daemon=True).start()

    while True:
        time.sleep(1)
