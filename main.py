import json, sys, threading, time, os, websocket, requests

sys.stdout.reconfigure(line_buffering=True)

def force_status_bubble(token):
    """ This hits the web API directly to set the bubble, just like the website does. """
    url = "https://discord.com/api/v9/users/@me/settings"
    headers = {"Authorization": token, "Content-Type": "application/json"}
    payload = {
        "custom_status": {
            "text": "rbxrise.com",
            "expires_at": None
        }
    }
    try:
        r = requests.patch(url, headers=headers, json=payload)
        if r.status_code == 200:
            print("[+] API: Status bubble successfully forced to rbxrise.com")
        else:
            print(f"[!] API Error: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"[!] Request Failed: {e}")

def run_gateway(token):
    """ This keeps you online 24/7 without any 'Playing' text. """
    while True:
        try:
            ws = websocket.WebSocket()
            ws.connect('wss://gateway.discord.gg/?v=9&encoding=json')
            
            # Get heartbeat
            hello = json.loads(ws.recv())
            hb_interval = hello['d']['heartbeat_interval'] / 1000
            
            # MOBILE properties (This is the secret to hiding 'Playing' and showing the phone)
            auth = {
                "op": 2,
                "d": {
                    "token": token,
                    "properties": {
                        "$os": "android",
                        "$browser": "Discord Android",
                        "$device": "Discord Android"
                    },
                    "presence": {
                        "status": "online",
                        "afk": False,
                        "activities": [] # This MUST be an empty list to kill "Playing..."
                    }
                }
            }
            ws.send(json.dumps(auth))
            print("[+] Gateway: Connected as Mobile. Activities cleared.")
            
            while True:
                time.sleep(hb_interval)
                ws.send(json.dumps({"op": 1, "d": None}))
                # Re-sync bubble every 30 mins
                force_status_bubble(token)
                
        except Exception as e:
            print(f"[!] Connection dropped: {e}. Retrying...")
            time.sleep(5)

if __name__ == "__main__":
    # Uses the variable you already have in Northflank
    token_str = os.getenv("DISCORDTOKENS")
    if token_str:
        for t in token_str.split(','):
            t = t.strip()
            # 1. Force the bubble immediately
            force_status_bubble(t)
            # 2. Start the 24/7 connection
            threading.Thread(target=run_gateway, args=(t,), daemon=True).start()
    
    while True:
        time.sleep(1)
