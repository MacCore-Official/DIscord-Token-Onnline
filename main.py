import json
import sys
import threading
import time
import os
import websocket
import requests
from colorama import Fore, init

# Force logs to show up immediately
sys.stdout.reconfigure(line_buffering=True)
init(autoreset=True)

# --- Configuration ---
# Set your message in Northflank using the Key: CUSTOM_STATUS
STATUS_TEXT = os.getenv("CUSTOM_STATUS", "Online Forever")
# online, dnd, idle
USER_STATUS = os.getenv("USER_STATUS", "online")

def set_custom_status(token, text):
    """This function sets the 'Custom Status' bubble text."""
    header = {"Authorization": token, "Content-Type": "application/json"}
    data = {"custom_status": {"text": text}}
    try:
        r = requests.patch("https://discord.com/api/v9/users/@me/settings", headers=header, json=data)
        if r.status_code == 200:
            print(f"{Fore.GREEN}[+] Custom Status set to: {text}")
        else:
            print(f"{Fore.RED}[!] Failed to set status bubble: {r.status_code}")
    except Exception as e:
        print(f"{Fore.RED}[!] Request Error: {e}")

def online_worker(token):
    try:
        # 1. Set the text bubble via API
        set_custom_status(token, STATUS_TEXT)

        # 2. Keep the account 'Online' via WebSocket
        ws = websocket.WebSocket()
        ws.connect('wss://gateway.discord.gg/?v=9&encoding=json')
        
        hello = json.loads(ws.recv())
        heartbeat_interval = hello['d']['heartbeat_interval']
        
        # Identity payload (No 'game' activity included here)
        auth = {
            "op": 2,
            "d": {
                "token": token,
                "properties": {"$os": "linux", "$browser": "Chrome", "$device": ""},
                "presence": {"status": USER_STATUS, "afk": False}
            }
        }
        
        ws.send(json.dumps(auth))
        print(f"{Fore.GREEN}[+] WebSocket Connected for {token[:15]}...")

        while True:
            time.sleep(heartbeat_interval / 1000)
            ws.send(json.dumps({"op": 1, "d": None}))
            
    except Exception as e:
        print(f"{Fore.RED}[!] Error: {e}")

if __name__ == "__main__":
    raw_tokens = os.getenv("DISCORDTOKENS") or ""
    tokens = [t.strip() for t in raw_tokens.split(",") if t.strip()]

    if not tokens:
        print(f"{Fore.RED}[!] No tokens found in DISCORDTOKENS variable.")
        sys.exit(1)

    print(f"{Fore.CYAN}--- Setting Normal Custom Status ---")
    for token in tokens:
        threading.Thread(target=online_worker, args=(token,), daemon=True).start()

    while True:
        time.sleep(1)
