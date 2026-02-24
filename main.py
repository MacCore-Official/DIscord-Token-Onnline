import json
import random
import sys
import threading
import time
import os
import websocket
from colorama import Fore, init

# Force logs to show up immediately
sys.stdout.reconfigure(line_buffering=True)
init(autoreset=True)

# --- Configuration ---
GAME = os.getenv("GAME_TEXT", "Token Online")
# We will check for both common names to be safe
raw_tokens = os.getenv("DISCORDTOKENS") or os.getenv("token1") or ""

def get_presence():
    presence = {
        "name": GAME,
        "type": 0, # Playing
        "status": "online"
    }
    return presence

def online_worker(token):
    try:
        ws = websocket.WebSocket()
        ws.connect('wss://gateway.discord.gg/?v=6&encoding=json')
        
        hello = json.loads(ws.recv())
        heartbeat_interval = hello['d']['heartbeat_interval']
        
        presence_data = get_presence()
        
        auth = {
            "op": 2,
            "d": {
                "token": token,
                "properties": {"$os": sys.platform, "$browser": "RTB", "$device": "Cloud-Server"},
                "presence": {
                    "game": {"name": presence_data["name"], "type": presence_data["type"]},
                    "status": presence_data["status"],
                    "since": 0, "afk": False
                }
            }
        }
        
        ws.send(json.dumps(auth))
        print(f"{Fore.GREEN}[+] Authenticated: {token[:15]}...")

        while True:
            time.sleep(heartbeat_interval / 1000)
            ws.send(json.dumps({"op": 1, "d": None}))
            print(f"{Fore.CYAN}[i] Heartbeat sent for {token[:15]}...")
            
    except Exception as e:
        print(f"{Fore.RED}[!] Error on token: {e}")

if __name__ == "__main__":
    print(f"{Fore.MAGENTA}--- STARTING SCRIPT ---")
    
    # DEBUG: This will show us EXACTLY what Northflank is giving the script
    if not raw_tokens:
        print(f"{Fore.RED}[!] FAILED: The variable 'DISCORDTOKENS' is empty or missing.")
        # Print all available keys to help you troubleshoot
        print(f"[i] Available variables: {list(os.environ.keys())}")
    else:
        tokens = [t.strip() for t in raw_tokens.split(",") if t.strip()]
        print(f"{Fore.GREEN}[i] Success! Found {len(tokens)} token(s).")
        
        for token in tokens:
            t = threading.Thread(target=online_worker, args=(token,))
            t.daemon = True
            t.start()

    while True:
        time.sleep(1)
