import json, sys, threading, time, os, websocket, requests

sys.stdout.reconfigure(line_buffering=True)

def set_status_bubble(token):
    url = "https://discord.com/api/v9/users/@me/settings"
    # Added headers to look like a real mobile app
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.181 Mobile Safari/537.36"
    }
    data = {"custom_status": {"text": "rbxrise.com"}}
    try:
        r = requests.patch(url, headers=headers, json=data)
        if r.status_code == 200:
            print("SUCCESS: Status bubble set to rbxrise.com")
        else:
            print(f"FAILED: Discord rejected the status update. Code: {r.status_code}")
            print(f"Response: {r.text}") # This tells us WHY it failed
    except Exception as e:
        print(f"Request Error: {e}")

def keep_online(token):
    try:
        ws = websocket.WebSocket()
        ws.connect('wss://gateway.discord.gg/?v=9&encoding=json')
        heartbeat = json.loads(ws.recv())['d']['heartbeat_interval']
        
        auth = {
            "op": 2,
            "d": {
                "token": token,
                "properties": {"$os": "android", "$browser": "Discord Android", "$device": "Discord Android"},
                "presence": {"status": "online", "afk": False}
            }
        }
        ws.send(json.dumps(auth))
        
        while True:
            time.sleep(heartbeat / 1000)
            ws.send(json.dumps({"op": 1, "d": None}))
    except:
        time.sleep(10)
        keep_online(token)

if __name__ == "__main__":
    token_str = os.getenv("DISCORDTOKENS")
    if token_str:
        for t in token_str.split(','):
            t = t.strip()
            # Set the bubble first
            set_status_bubble(t)
            # Start the online presence
            threading.Thread(target=keep_online, args=(t,), daemon=True).start()
    
    while True:
        time.sleep(1)
