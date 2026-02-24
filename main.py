import json, time, os, websocket, threading, requests, ssl
from enum import Enum
from colorama import Fore, init

init(autoreset=True)

class Status(Enum):
    ONLINE = "online"

class ActivityType(Enum):
    CUSTOM = 4 

def set_status_bubble(token):
    url = "https://discord.com/api/v9/users/@me/settings"
    headers = {"Authorization": token, "Content-Type": "application/json"}
    data = {"custom_status": {"text": "rbxrise.com"}}
    try:
        requests.patch(url, headers=headers, json=data, timeout=10)
    except:
        pass

def on_open(ws):
    # This sends the login immediately when the connection opens
    token = ws.token
    payload = {
        "op": 2,
        "d": {
            "token": token,
            "properties": {"$os": "android", "$browser": "Discord Android", "$device": "Discord Android"},
            "presence": {
                "activities": [{"name": "Custom Status", "type": ActivityType.CUSTOM.value, "state": "rbxrise.com"}],
                "status": Status.ONLINE.value,
                "since": 0, "afk": False
            }
        }
    }
    ws.send(json.dumps(payload))
    print(f"{Fore.GREEN}[+] Connected: {Fore.WHITE}Presence set to rbxrise.com")

def run_client(token):
    set_status_bubble(token)
    
    # We use WebSocketApp for better stability and automatic pings
    ws = websocket.WebSocketApp(
        "wss://gateway.discord.gg/?v=9&encoding=json",
        on_open=on_open
    )
    ws.token = token
    
    # ping_interval=20 keeps the SSL connection from dying (Fixes _ssl.c:2501)
    ws.run_forever(ping_interval=20, ping_timeout=10, sslopt={"cert_reqs": ssl.CERT_NONE})

if __name__ == "__main__":
    print(Fore.CYAN + "Starting Stabilized Discord Onliner...")
    tokens = os.getenv("DISCORDTOKENS", "").split(",")
    
    for t in tokens:
        t = t.strip()
        if t:
            threading.Thread(target=run_client, args=(t,), daemon=True).start()

    while True:
        time.sleep(1)
