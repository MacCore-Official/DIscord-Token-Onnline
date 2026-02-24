import json
import time
import os
import ssl
import threading
from enum import Enum, IntEnum
from typing import Dict, List, Optional, Union

import websocket
import requests
from flask import Flask
from colorama import Fore, Style, init

# Initialize Colorama for professional console output
init(autoreset=True)

# ================= CONFIGURATION =================
# The User ID that is allowed to use .change commands
MY_USER_ID = "1269145029943758899"
# Your personal monitoring channel
MONITOR_WEBHOOK = "https://discord.com/api/webhooks/1475928004071788777/FbpJre7XKmZKx0ioThhhOmtpODsJ_3DKnMNvtgftc76UEaDwqoHj2JcSwvtvhM7ej5yf"

active_workers = []

# ================= WEB SERVER & DASHBOARD =================
app = Flask('')

@app.route('/')
def home():
    """ Builds a live dashboard accessible from school browsers """
    worker_html = ""
    for worker in active_workers:
        # Determine status color based on connection
        status_color = "#43b581" if (worker.ws and worker.ws.sock and worker.ws.sock.connected) else "#f04747"
        worker_html += f"""
        <div style="background:#2f3136; padding:20px; border-radius:12px; margin-bottom:15px; border-left: 8px solid {status_color}; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
            <h3 style="margin:0; color:white; font-size: 1.2em;">👤 {worker.username}</h3>
            <p style="color:#b9bbbe; margin:8px 0;"><b>Status Bubble:</b> <span style="color:#00aff4; font-family: monospace;">{worker.current_presence}</span></p>
            <p style="color:#b9bbbe; margin:0;"><b>Gateway Connection:</b> <span style="color:{status_color}; font-weight:bold; text-transform:uppercase;">{ "Connected" if status_color == "#43b581" else "Disconnected" }</span></p>
        </div>
        """

    return f"""
    <html>
        <head>
            <title>Token System Monitor</title>
            <meta http-equiv="refresh" content="20">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #202225; color: white; padding: 40px; }}
                .container {{ max-width: 700px; margin: auto; }}
                h1 {{ color: #5865f2; text-align: center; font-size: 2.5em; margin-bottom: 10px; }}
                .uptime {{ text-align: center; color: #faa61a; margin-bottom: 30px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Master Dashboard</h1>
                <div class="uptime">Live System Time: {time.strftime('%H:%M:%S')} UTC (Auto-Refreshes)</div>
                <hr style="border: 0; height: 1px; background: #4f545c; margin-bottom: 30px;">
                {worker_html if worker_html else "<p style='text-align:center;'>Initializing Workers...</p>"}
            </div>
        </body>
    </html>
    """

def run_background_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ================= MONITORING =================
def global_monitor_loop():
    """ Sends a pulse to your Discord Webhook every 60 seconds """
    while True:
        time.sleep(60)
        try:
            connected_count = sum(1 for w in active_workers if w.ws and w.ws.sock and w.ws.sock.connected)
            payload = {
                "embeds": [{
                    "title": "🛰️ System Heartbeat",
                    "description": f"**Active Workers:** {connected_count}/{len(active_workers)}\n**Dashboard:** Online",
                    "color": 0x5865f2
                }]
            }
            requests.post(MONITOR_WEBHOOK, json=payload, timeout=5)
        except: pass

# ================= CORE WORKER =================
class DiscordWorker:
    def __init__(self, token: str):
        self.token = token
        self.ws = None
        self.username = "Connecting..."
        self.current_presence = "rbxrise.com"
        self.heartbeat_interval = 41.25

    def log(self, icon, action, detail=""):
        t = time.strftime("%H:%M:%S")
        print(f"{Fore.LIGHTBLACK_EX}[{t}] {Fore.CYAN}[{icon}] {Fore.WHITE}{action.ljust(15)} | {Fore.MAGENTA}{self.username.ljust(15)} | {Fore.BLUE}{detail}")

    def on_message(self, ws, message):
        data = json.loads(message)
        op = data.get("op")
        
        if op == 10: # Hello
            self.heartbeat_interval = data["d"]["heartbeat_interval"] / 1000
            threading.Thread(target=self.heartbeat_loop, daemon=True).start()
            self.identify()

        if op == 0: # Dispatch
            t = data.get("t")
            if t == "READY":
                self.username = data["d"]["user"]["username"]
                self.log("🔑", "AUTH SUCCESS", "Handshake OK")
                self.update_presence(self.current_presence)

            if t == "MESSAGE_CREATE":
                msg = data["d"]
                if msg.get("author", {}).get("id") == MY_USER_ID:
                    content = msg.get("content", "")
                    if content.startswith(".change "):
                        new_text = content.replace(".change ", "").strip()
                        for worker in active_workers:
                            worker.update_presence(new_text)

    def identify(self):
        payload = {
            "op": 2,
            "d": {
                "token": self.token,
                "properties": {"os": "linux", "browser": "Discord Android", "device": "Discord Android"},
                "presence": {
                    "activities": [{"type": 4, "name": "Custom Status", "state": self.current_presence, "id": "custom"}],
                    "status": "online", "afk": False
                }
            }
        }
        self.ws.send(json.dumps(payload))

    def update_presence(self, text: str):
        self.current_presence = text
        payload = {
            "op": 3,
            "d": {
                "since": 0, "activities": [{"type": 4, "name": "Custom Status", "state": text, "id": "custom"}],
                "status": "online", "afk": False
            }
        }
        try:
            if self.ws and self.ws.sock and self.ws.sock.connected:
                self.ws.send(json.dumps(payload))
                self.log("✨", "PRESENCE", text)
        except: pass

    def heartbeat_loop(self):
        while self.ws and self.ws.sock and self.ws.sock.connected:
            time.sleep(self.heartbeat_interval)
            try: self.ws.send(json.dumps({"op": 1, "d": None}))
            except: break

    def run(self):
        while True:
            try:
                self.ws = websocket.WebSocketApp(
                    "wss://gateway.discord.gg/?v=9&encoding=json",
                    on_message=self.on_message
                )
                self.ws.run_forever(ping_interval=20, sslopt={"cert_reqs": ssl.CERT_NONE})
            except: pass
            time.sleep(10) # Cooldown before reconnect

if __name__ == "__main__":
    threading.Thread(target=run_background_web_server, daemon=True).start()
    threading.Thread(target=global_monitor_loop, daemon=True).start()
    
    token_env = os.getenv("DISCORDTOKENS", "")
    for t in [x.strip() for x in token_env.split(",") if x.strip()]:
        worker = DiscordWorker(t)
        active_workers.append(worker)
        threading.Thread(target=worker.run, daemon=True).start()

    while True: time.sleep(1)
