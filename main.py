import json
import time
import os
import ssl
import threading
import random
from enum import Enum, IntEnum
from typing import Dict, List, Optional, Union

import websocket
import requests
from flask import Flask
from colorama import Fore, Style, init

# Initialize Colorama for professional console output
init(autoreset=True)

# ================= CONFIGURATION =================
MY_USER_ID = "1269145029943758899"
MONITOR_WEBHOOK = "https://discord.com/api/webhooks/1475928004071788777/FbpJre7XKmZKx0ioThhhOmtpODsJ_3DKnMNvtgftc76UEaDwqoHj2JcSwvtvhM7ej5yf"
active_workers = []

# ================= ENUMERATIONS =================
class Status(Enum):
    ONLINE = "online"
    DND = "dnd"
    IDLE = "idle"

class ActivityType(IntEnum):
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
    Resume = 6
    Reconnect = 7
    Hello = 10
    HeartbeatACK = 11

# ================= WEB SERVER =================
app = Flask('')

@app.route('/')
def health_check():
    return "Master Onliner is Systemically Operational."

def run_background_web_server():
    """ Keeps Northflank from putting the script to sleep """
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ================= MONITORING =================
def send_webhook_log(message: str):
    """ Sends a heartbeat update to your Discord Webhook every 10s """
    payload = {
        "embeds": [{
            "title": "System Monitor",
            "description": message,
            "color": 0x00ff00,
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())
        }]
    }
    try:
        requests.post(MONITOR_WEBHOOK, json=payload, timeout=5)
    except:
        pass

def global_monitor_loop():
    """ Background thread to send the 10-second webhook update """
    while True:
        time.sleep(10)
        worker_count = len(active_workers)
        status_text = "System Healthy" if worker_count > 0 else "System Warning: No Workers"
        send_webhook_log(f"**Status:** {status_text}\n**Active Tokens:** {worker_count}\n**Uptime:** Active")

# ================= CORE LOGIC =================
class DiscordWorker:
    def __init__(self, token: str):
        self.token = token
        self.ws = None
        self.username = "Connecting..."
        self.current_presence = "rbxrise.com"
        self.heartbeat_interval = 41250 / 1000

    def log(self, icon, action, detail=""):
        """ Professional Column-Based Logging """
        timestamp = time.strftime("%H:%M:%S")
        print(f"{Fore.LIGHTBLACK_EX}[{timestamp}] {Fore.CYAN}[{icon}] "
              f"{Fore.WHITE}{action.ljust(18)} | "
              f"{Fore.MAGENTA}{self.username.ljust(15)} | "
              f"{Fore.BLUE}{detail}")

    def on_message(self, ws, message):
        data = json.loads(message)
        op = data.get("op")
        t = data.get("t")

        # OP 10: HELLO (First contact)
        if op == OPCodes.Hello.value:
            self.heartbeat_interval = data["d"]["heartbeat_interval"] / 1000
            threading.Thread(target=self.heartbeat_loop, daemon=True).start()
            self.identify()

        # OP 0: DISPATCH (Events)
        if op == OPCodes.Dispatch.value:
            if t == "READY":
                self.username = data["d"]["user"]["username"]
                self.log("🔑", "AUTH SUCCESS", "Handshake Complete")
                self.update_presence(self.current_presence)

            if t == "MESSAGE_CREATE":
                msg = data["d"]
                # Master Control Logic
                if msg.get("author", {}).get("id") == MY_USER_ID:
                    content = msg.get("content", "")
                    if content.startswith(".change "):
                        new_text = content.replace(".change ", "").strip()
                        print(f"\n{Fore.YELLOW}[!] Master Override Initiated: {new_text}")
                        for worker in active_workers:
                            worker.update_presence(new_text)

    def identify(self):
        """ Authenticates the token to the gateway """
        payload = {
            "op": OPCodes.Identify.value,
            "d": {
                "token": self.token,
                "properties": {
                    "$os": "linux",
                    "$browser": "Discord Android",
                    "$device": "Discord Android"
                },
                "presence": {
                    "activities": [{
                        "type": ActivityType.CUSTOM.value,
                        "name": "Custom Status",
                        "state": self.current_presence,
                        "id": "custom"
                    }],
                    "status": Status.ONLINE.value,
                    "since": 0,
                    "afk": False
                }
            }
        }
        self.ws.send(json.dumps(payload))

    def update_presence(self, text: str):
        """ Forces a live status change via Gateway OP 3 """
        self.current_presence = text
        payload = {
            "op": OPCodes.PresenceUpdate.value,
            "d": {
                "since": 0,
                "activities": [{
                    "type": ActivityType.CUSTOM.value,
                    "name": "Custom Status",
                    "state": text,
                    "id": "custom"
                }],
                "status": Status.ONLINE.value,
                "afk": False
            }
        }
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps(payload))
            self.log("✨", "PRESENCE PUSH", text)

    def heartbeat_loop(self):
        """ Keeps the connection from timing out """
        while self.ws and self.ws.sock and self.ws.sock.connected:
            time.sleep(self.heartbeat_interval)
            try:
                self.ws.send(json.dumps({"op": OPCodes.Heartbeat.value, "d": None}))
            except:
                break

    def run(self):
        """ Reconnect loop to ensure 24/7 uptime """
        while True:
            try:
                self.ws = websocket.WebSocketApp(
                    "wss://gateway.discord.gg/?v=9&encoding=json",
                    on_message=self.on_message,
                    on_error=lambda ws, err: self.log("❌", "SOCKET ERROR", str(err)),
                    on_close=lambda ws, s, m: self.log("🔌", "DISCONNECTED", "Retrying...")
                )
                self.ws.run_forever(ping_interval=20, sslopt={"cert_reqs": ssl.CERT_NONE})
            except Exception as e:
                self.log("⚠️", "CRITICAL ERROR", str(e))
            time.sleep(10)

# ================= BOOTSTRAP =================
def print_banner():
    print(Fore.RED + Style.BRIGHT + r"""
  ██████╗ ██╗ ██████╗ ██████╗ ██╗   ██╗ ██╗███████╗
  ██╔══██╗██║██╔════╝ ██╔════╝╚██╗ ██╔╝██╔╝██╔════╝
  ██████╔╝██║██║  ███╗██║  ███╗╚████╔╝ ╚═╝ ███████╗
  ██╔═══╝ ██║██║   ██║██║   ██║ ╚██╔╝      ╚════██║
  ██║     ██║╚██████╔╝╚██████╔╝  ██║       ███████║
  ╚═╝     ╚═╝ ╚═════╝  ╚═════╝   ╚═╝       ╚══════╝
    """ + Fore.CYAN + "      MASTER CONTROLLER | VERSION 4.0 | WEBHOOK ENABLED\n")

if __name__ == "__main__":
    print_banner()
    
    # Start Keep-Alive Web Server
    threading.Thread(target=run_background_web_server, daemon=True).start()
    
    # Start Webhook Monitoring
    threading.Thread(target=global_monitor_loop, daemon=True).start()
    
    # Initialize Workers
    tokens = os.getenv("DISCORDTOKENS", "").split(",")
    valid_tokens = [t.strip() for t in tokens if t.strip()]
    
    print(f"{Fore.GREEN}[!] Detected {len(valid_tokens)} tokens. Spawning threads...\n")
    
    for token in valid_tokens:
        worker = DiscordWorker(token)
        active_workers.append(worker)
        threading.Thread(target=worker.run, daemon=True).start()

    # Keep Main Thread Alive
    while True:
        time.sleep(1)
