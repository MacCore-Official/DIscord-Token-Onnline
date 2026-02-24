import json, sys, threading, time, os, websocket, requests

# Force immediate logs
sys.stdout.reconfigure(line_buffering=True)

def set_status_bubble(token, text):
    # This specifically target the "Normal" status bubble
    try:
        requests.patch("https://discord.com/api/v9/users/@me/settings", 
                       headers={"Authorization": token}, 
                       json={"custom_status": {"text": text}})
        print(f"Status bubble updated to: {text}")
    except: pass

def keep_online(token):
    ws = websocket.WebSocket()
    ws.connect('wss://gateway.discord.gg/?v=9&encoding=json')
    heartbeat = json.loads(ws.recv())['d']['heartbeat_interval']
    
    # We send NO 'game' or 'activity' in this payload
    auth = {"op": 2, "d": {"token": token, "properties": {"$os": "linux"}, "presence": {"status": "online", "afk": False}}}
    ws.send(json.dumps(auth))
    
    while True:
        time.sleep(heartbeat / 1000)
        ws.send(json.dumps({"op": 1, "d": None}))

if __name__ == "__main__":
    token = os.getenv("DISCORDTOKENS")
    status_text = os.getenv("CUSTOM_STATUS", "Vibing")
    
    if token:
        # If you have multiple tokens separated by commas
        for t in token.split(','):
            t = t.strip()
            set_status_bubble(t, status_text)
            threading.Thread(target=keep_online, args=(t,), daemon=True).start()
    
    while True: time.sleep(1)
