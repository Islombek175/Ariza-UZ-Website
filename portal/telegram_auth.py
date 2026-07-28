import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl
from django.conf import settings

def verify_init_data(init_data, max_age=86400):
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None) or __import__("os").getenv("TELEGRAM_BOT_TOKEN")
    if not token or not init_data: return None
    values = dict(parse_qsl(init_data, keep_blank_values=True))
    received = values.pop("hash", "")
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(values.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received): return None
    if int(time.time()) - int(values.get("auth_date", 0)) > max_age: return None
    try: return json.loads(values["user"])
    except (KeyError, json.JSONDecodeError): return None
