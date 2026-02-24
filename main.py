import json, sys, threading, time, os, websocket, requests

# Force logs to show immediately
sys.stdout.reconfigure(line_buffering=True)

def set_status_bubble(token):
    # Hardcoded status bubble update
    url = "https://discord.com/api/v9/users/@me/settings"
    headers = {"Authorization": token, "Content-Type": "application/json"}
    data = {"custom_status": {"text": "rbxrise.com"}}
    try:
        r = requests.patch(url, headers=headers, json=data)
        print(f"Status set to rbxrise.com (Code: {r.status_code})")
    except Exception as e:
        print(f"Error setting bubble: {e}")

def keep_online(token):
    try:
        ws = websocket.WebSocket()
        ws.connect('wss://gateway.discord.gg/?v=9&encoding=json')
        heartbeat = json.loads(ws.recv())['d']['heartbeat_interval']
        
        # Identify as a Mobile device (this often helps status bubbles stay)
        # We send NO 'activities' array, which kills the "Playing" text
        auth = {
            "op": 2,
            "d": {
                "token": token,
                "properties": {"$os": "android", "$browser": "Discord Android", "$device": "Discord Android"},
                "presence": {"status": "online", "afk": False}
            }
        }
        ws.send(json.dumps(auth))
        print("Connected to WebSocket as Mobile (No Game Activity)")
        
        while True:
            time.sleep(heartbeat / 1000)
            ws.send(json.dumps({"op": 1, "d": None}))
    except Exception as e:
        print(f"WS Error: {e}")

if __name__ == "__main__":
    # Get your token from your existing DISCORDTOKENS secret
    token_str = os.getenv("DISCORDTOKENS")
    if token_str:
        for t in token_str.split(','):
            t = t.strip()
            set_status_bubble(t)
            threading.Thread(target=keep_online, args=(t,), daemon=True).start()
    
    while True:
        time.sleep(1)
