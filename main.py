import json, time, os, websocket, threading, requests, ssl
from enum import Enum
from colorama import Fore, init

init(autoreset=True)

# YOUR CONFIG
MY_USER_ID = "1269145029943758899"

class ActivityType(Enum):
    CUSTOM = 4 

# This list will hold all active websocket connections
active_connections = []

def update_all_statuses(new_text):
    """Hits the API for every token to change the bubble globally."""
    tokens = os.getenv("DISCORDTOKENS", "").split(",")
    for t in tokens:
        t = t.strip()
        if t:
            url = "https://discord.com/api/v9/users/@me/settings"
            headers = {"Authorization": t, "Content-Type": "application/json"}
            data = {"custom_status": {"text": new_text}}
            try:
                requests.patch(url, headers=headers, json=data, timeout=5)
            except: pass
    print(f"{Fore.YELLOW}[!] Status changed to: {new_text}")

def on_message(ws, message):
    data = json.loads(message)
    
    # Check if the message is a 'Message Create' event
    if data.get("t") == "MESSAGE_CREATE":
        msg = data["d"]
        content = msg.get("content", "")
        author_id = msg.get("author", {}).get("id")

        # ONLY trigger if the message is from YOU and starts with .change
        if author_id == MY_USER_ID and content.startswith(".change "):
            new_status = content.replace(".change ", "").strip()
            update_all_statuses(new_status)

def on_open(ws):
    payload = {
        "op": 2,
        "d": {
            "token": ws.token,
            "properties": {"$os": "android", "$browser": "Discord Android", "$device": "Discord Android"},
            "presence": {
                "activities": [{"name": "Custom Status", "type": ActivityType.CUSTOM.value, "state": "rbxrise.com"}],
                "status": "online",
                "since": 0, "afk": False
            }
        }
    }
    ws.send(json.dumps(payload))
    print(f"{Fore.GREEN}[+] Worker online for token ending in ...{ws.token[-5:]}")

def run_client(token):
    ws = websocket.WebSocketApp(
        "wss://gateway.discord.gg/?v=9&encoding=json",
        on_open=on_open,
        on_message=on_message
    )
    ws.token = token
    ws.run_forever(ping_interval=20, sslopt={"cert_reqs": ssl.CERT_NONE})

if __name__ == "__main__":
    print(Fore.CYAN + "Starting Remote-Controlled Discord Onliner...")
    tokens = os.getenv("DISCORDTOKENS", "").split(",")
    
    for t in tokens:
        t = t.strip()
        if t:
            threading.Thread(target=run_client, args=(t,), daemon=True).start()

    while True:
        time.sleep(1)
