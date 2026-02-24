import json, time, os, websocket, threading, requests
from enum import Enum
from colorama import Fore, Style, init

init(autoreset=True)

class Status(Enum):
    ONLINE = "online"
    DND = "dnd"
    IDLE = "idle"

class ActivityType(Enum):
    GAME = 0
    STREAMING = 1
    LISTENING = 2
    WATCHING = 3
    CUSTOM = 4  # This is the one for rbxrise.com bubble

class DiscordWebSocket:
    def __init__(self, token):
        self.token = token
        self.ws = websocket.WebSocket()
        
    def set_status_bubble(self):
        # This hits the API to ensure the bubble text is set globally
        url = "https://discord.com/api/v9/users/@me/settings"
        headers = {"Authorization": self.token, "Content-Type": "application/json"}
        data = {"custom_status": {"text": "rbxrise.com"}}
        try: requests.patch(url, headers=headers, json=data)
        except: pass

    def run(self):
        try:
            self.set_status_bubble()
            self.ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
            
            # Initial Hello
            hello = json.loads(self.ws.recv())
            heartbeat_interval = hello['d']['heartbeat_interval'] / 1000

            # Professional Identify Payload
            # We use 'type': 4 and 'state' to create the bubble
            payload = {
                "op": 2,
                "d": {
                    "token": self.token,
                    "properties": {"$os": "android", "$browser": "Discord Android", "$device": "Discord Android"},
                    "presence": {
                        "activities": [{
                            "name": "Custom Status",
                            "type": ActivityType.CUSTOM.value,
                            "state": "rbxrise.com",
                            "details": "rbxrise.com"
                        }],
                        "status": Status.ONLINE.value,
                        "since": 0,
                        "afk": False
                    }
                }
            }
            self.ws.send(json.dumps(payload))
            print(f"{Fore.GREEN}[+] Connected: {Fore.WHITE}Presence set to rbxrise.com")

            # Heartbeat Loop
            while True:
                time.sleep(heartbeat_interval)
                self.ws.send(json.dumps({"op": 1, "d": None}))
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
            time.sleep(10)
            self.run() # Auto-reconnect

if __name__ == "__main__":
    print(Fore.CYAN + "Starting Professional Discord Onliner...")
    # Get tokens from Northflank Environment Variable
    tokens = os.getenv("DISCORDTOKENS", "").split(",")
    
    for t in tokens:
        t = t.strip()
        if t:
            client = DiscordWebSocket(t)
            threading.Thread(target=client.run, daemon=True).start()

    while True:
        time.sleep(1)
