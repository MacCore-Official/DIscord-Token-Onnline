import json
import random
import sys
import threading
import time
import os
import websocket
from colorama import Fore, init

# Force logs to show up immediately in Northflank
sys.stdout.reconfigure(line_buffering=True)
init(autoreset=True)

# --- Configuration ---
GAME = os.getenv("GAME_TEXT", "Token Online")
STREAM_URL = os.getenv("STREAM_URL", "https://twitch.tv/directory")
STATUS_TYPE = os.getenv("STATUS_TYPE", "Playing")  # Playing, Streaming, Watching, Listening
USER_STATUS = os.getenv("USER_STATUS", "online")  # online, dnd, idle
RANDOM_MODE = os.getenv("RANDOM_MODE", "True").lower() == "true"

def get_presence():
    if RANDOM_MODE:
        current_type = random.choice(['Playing', 'Streaming', 'Watching', 'Listening'])
        current_status = random.choice(['online', 'dnd', 'idle'])
    else:
        current_type = STATUS_TYPE
        current_status = USER_STATUS

    type_map = {"Playing": 0, "Streaming": 1, "Listening": 2, "Watching": 3}
    t_int = type_map.get(current_type, 0)

    game_name = GAME
    if RANDOM_MODE:
        if current_type == "Playing": game_name = random.choice(["Minecraft", "Roblox", "Fortnite"])
        if current_type == "Listening": game_name = random.choice(["Spotify", "SoundCloud"])

    presence = {
        "name": game_name,
        "type": t_int,
        "status": current_status
    }
    if t_int == 1: presence["url"] = STREAM_URL
    
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
                    "game": {"name": presence_data["name"], "type": presence_data["type"], "url": presence_data.get("url")},
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
        print(f"{Fore.RED}[!] Error on token {token[:10]}: {e}")

if __name__ == "__main__":
    print(f"""{Fore.MAGENTA}
    ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄  ▄    ▄  ▄▄▄▄▄▄▄▄▄▄▄ 
    ▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░▌  ▐░▌▐░░░░░░░░░░░▌
     ▀▀▀▀█░█▀▀▀▀ ▐░█▀▀▀▀▀▀▀█░▌▐░▌ ▐░▌ ▐░█▀▀▀▀▀▀▀▀▀ 
          ▐░▌     ▐░▌       ▐░▌▐░▌▐░▌  ▐░▌         
          ▐░▌     ▐░▌       ▐░▌▐░▌░▌   ▐░█▄▄▄▄▄▄▄▄▄ 
          ▐░▌     ▐░▌       ▐░▌▐░░▌    ▐░░░░░░░░░░░▌
    """)
    
    # Correctly reading from your Northflank Environment Variable
    raw_tokens = os.getenv("DISCORDTOKENS", "")
    tokens = [t.strip() for t in raw_tokens.split(",") if t.strip()]

    if not tokens:
        print(f"{Fore.RED}[!] CRITICAL: No tokens found! Please check DISCORDTOKENS in Northflank.")
        sys.exit(1)

    print(f"{Fore.YELLOW}[i] Found {len(tokens)} tokens. Starting connection threads...")
    
    for token in tokens:
        t = threading.Thread(target=online_worker, args=(token,))
        t.daemon = True
        t.start()

    # Keep the main process running
    while True:
        time.sleep(1)
