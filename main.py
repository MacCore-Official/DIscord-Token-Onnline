import json, sys, threading, time, os, websocket, requests

sys.stdout.reconfigure(line_buffering=True)

def set_status_bubble(token):
    url = "https://discord.com/api/v9/users/@me/settings"
    headers = {"Authorization": token, "Content-Type": "application/json"}
    # This payload is what makes it stick
    data = {
        "custom_status": {
            "text": "rbxrise.com",
            "expires_at": None
        }
    }
    try:
        requests.patch(url, headers=headers, json=data)
        print("Successfully pushed rbxrise.com to Discord servers.")
    except: pass

def keep_online(token):
    while True: # This loop ensures it restarts if it crashes
        try:
            ws = websocket.WebSocket()
            ws.connect('wss://gateway.discord.gg/?v=9&encoding=json')
            
            # Get heartbeat interval from Discord
            hello = json.loads(ws.recv())
            heartbeat_interval = hello['d']['heartbeat_interval'] / 1000
            
            # Mobile identify (keeps you 'Online' without a game)
            auth = {
                "op": 2,
                "d": {
                    "token": token,
                    "properties": {"$os": "android", "$browser": "Discord Android", "$device": "Discord Android"},
                    "presence": {"status": "online", "afk": False}
                }
            }
            ws.send(json.dumps(auth))
            print("Connected! You are now 'Online' on Mobile.")
            
            # The Infinite Heartbeat
            while True:
                time.sleep(heartbeat_interval)
                ws.send(json.dumps({"op": 1, "d": None}))
                # Re-apply status bubble every hour just to be safe
                set_status_bubble(token) 
                
        except Exception as e:
            print(f"Connection lost, reconnecting in 10s... Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    token_str = os.getenv("DISCORDTOKENS")
    if token_str:
        for t in token_str.split(','):
            t = t.strip()
            # Start the worker for each token
            threading.Thread(target=keep_online, args=(t,), daemon=True).start()
    
    # Keep the main script running forever
    while True:
        time.sleep(1)
