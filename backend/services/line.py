import traceback  # เพิ่ม import ด้านบน
import sys        # เพิ่ม import ด้านบน
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, PushMessageRequest,
    TextMessage, FlexMessage, FlexBubble, FlexBox, FlexText  # เพิ่ม FlexBubble, FlexBox, FlexText เข้ามา
)
import requests
from config import config

configuration = None
handler = None

if config.LINE_CHANNEL_TOKEN:
    configuration = Configuration(access_token=config.LINE_CHANNEL_TOKEN)
    if config.LINE_CHANNEL_SECRET:
        handler = WebhookHandler(config.LINE_CHANNEL_SECRET)

def push_line_message(text: str, user_id: str = None):
    uid = user_id or config.LINE_USER_ID
    print(f"LINE Push: {text} to {uid}")
    if not uid or not configuration: 
        print("❌ LINE Push Failed: Missing User ID or Token")
        return False
    try:
        with ApiClient(configuration) as api_client:
            MessagingApi(api_client).push_message(
                PushMessageRequest(to=uid, messages=[TextMessage(text=text)])
            )
        print(f"✅ LINE push success to {uid}")
        return True
    except Exception as e:
        # เปิดเผย Error จริงๆ!
        print(f"❌ LINE Push Error: {e}")
        traceback.print_exc() 
        return False

def push_flex_message(alt_text: str, flex_dict: dict, user_id: str = None):
    uid = user_id or config.LINE_USER_ID
    if not uid or not config.LINE_CHANNEL_TOKEN:
        print("❌ LINE Push Failed: Missing User ID or Token")
        return False

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {config.LINE_CHANNEL_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": uid,
        "messages": [
            {
                "type": "flex",
                "altText": alt_text,
                "contents": flex_dict   # ส่ง dict ที่สร้างจาก utils.py โดยตรง
            }
        ]
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            print(f"✅ Flex pushed to {uid}")
            return True
        else:
            print(f"❌ LINE Flex Push Error: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ LINE Flex Push Exception: {e}")
        return False