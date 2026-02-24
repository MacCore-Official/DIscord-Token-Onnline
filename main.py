import json, time, os, websocket, threading, requests, ssl
from colorama import Fore, init

init(autoreset=True)

MY_USER_ID = "1269145029943758899"
active_workers = [] # Store workers here to trigger live updates

class DiscordWorker:
    def __init__(self, token):
        self.token = token
        self.ws = None

    def send_presence(self, text):
        """This is the exact structure Discord uses for the bubble."""
        payload = {
            "op": 3,
            "d": {
                "since": 0,
                "activities": [{
                    "type": 4, # Custom Activity
                    "name": "Custom Status",
                    "state": text,
                    "id": "custom"
                }],
                "status": "online",
                "afk": False
            }
        }
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps(payload))

    def on_message(self, ws, message):
        data = json.loads(message)
        if data.get("t") == "MESSAGE_CREATE":
            msg = data["d"]
            if msg.get("author", {}).get("id") == MY_USER_ID:
                content = msg.get("content", "")
                if content.startswith(".change "):
                    new_text = content.replace(".change ", "").strip()
                    print(f"{Fore.YELLOW}[!] Triggering mass update to: {new_text}")
                    # Update EVERY worker currently running
                    for worker in active_workers:
                        worker.send_presence(new_text)

    def run(self):
        def on_open(ws):
            self.ws = ws
            self.send_presence("rbxrise.com") # Default status
            print(f"{Fore.GREEN}[+] Worker Active: ...{self.token[-5:]}")

        self.ws = websocket.WebSocketApp(
            "wss://gateway.discord.gg/?v=9&encoding=json",
            on_open=on_open,
            on_message=self.on_message
        )
        self.ws.token = self.token
        self.ws.run_forever(ping_interval=20, sslopt={"cert_reqs": ssl.CERT_NONE})

if __name__ == "__main__":
    print(Fore.CYAN + "Starting Multi-Sync Discord Onliner...")
    tokens = os.getenv("DISCORDTOKENS", "").split(",")
    
    for t in tokens:
        t = t.strip()
        if t:
            worker = DiscordWorker(t)
            active_workers.append(worker)
            threading.Thread(target=worker.run, daemon=True).start()

    while True:
        time.sleep(1)
