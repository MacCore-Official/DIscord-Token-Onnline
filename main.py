import json, sys, threading, time, os, websocket, requests

# Force logs to show immediately
sys.stdout.reconfigure(line_buffering=True)

def set_status_bubble(token):
    """ This hits the web API directly to set the bubble. """
    url = "https://discord.com/api/v9/users/@me/settings"
    headers = {"Authorization": token, "Content-Type": "application/json"}
    # The 'expires_at: None' makes it stay forever
    data = {"custom_status": {"text": "rbxrise.com", "expires_at": None}}
    try:
        r = requests.patch(url, headers=headers, json=data)
        if r.status_code == 200:
            print("[+] API Success: Bubble set to rbxrise.com")
        else:
            print(f"[!] API Failed: {r.status_code}")
    except: pass

def keep_online(token):
    while True:
        try:
            ws = websocket.WebSocket()
            ws.connect('wss://gateway.discord.gg/?v=9&encoding=json')
            hb = json.loads(ws.recv())['d']['heartbeat_interval'] / 1000
            
            # This 'Identify' packet is what tells Discord you are on a PHONE
            # By leaving 'activities' as an EMPTY LIST [], we kill the "Playing" text
            auth = {
                "op": 2,
                "d": {
                    "token": token,
                    "properties": {"$os": "android", "$browser": "Discord Android", "$device": "Discord Android"},
                    "presence": {"status": "online", "afk": False, "activities": []} 
                }
            }
            ws.send(json.dumps(auth))
            print("[+] Gateway: Connected (Activities Cleared)")
            
            while True:
                time.sleep(hb)
                ws.send(json.dumps({"op": 1, "d": None}))
        except:
            time.sleep(10)

if __name__ == "__main__":
    token_str = os.getenv("DISCORDTOKENS")
    if token_str:
        for t in token_str.split(','):
            t = t.strip()
            set_status_bubble(t)
            threading.Thread(target=keep_online, args=(t,), daemon=True).start()
    
    while True: time.sleep(1)
