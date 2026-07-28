import json
import os
import urllib.request

def send_telegram(user, text):
    token=os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or not user.telegram_id: return False
    payload=json.dumps({"chat_id":user.telegram_id,"text":text}).encode()
    request=urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage",data=payload,headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(request,timeout=5) as response: return response.status==200
    except Exception: return False
