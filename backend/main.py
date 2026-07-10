import os
import json
import time
import requests
from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, MessageEvent, TextMessage
from linebot.exceptions import InvalidSignatureError
from dotenv import load_dotenv
import certifi
import paho.mqtt.client as mqtt

load_dotenv()

# ================== Configuration ==================
NETPIE_CLIENT_ID = os.getenv("NETPIE_CLIENT_ID", "")
NETPIE_TOKEN = os.getenv("NETPIE_TOKEN", "")
NETPIE_SECRET = os.getenv("NETPIE_SECRET", "")
NETPIE_BROKER = os.getenv("NETPIE_BROKER", "broker.netpie.io")

LINE_CHANNEL_TOKEN = os.getenv("LINE_CHANNEL_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# Environment detection
IS_VERCEL = os.getenv("VERCEL", "0") == "1"
USE_MQTT = os.getenv("USE_MQTT", "1" if not IS_VERCEL else "0") == "1"

# ================== MQTT Client (only if USE_MQTT = True) ==================
mqtt_client = None

def get_mqtt_client():
    """สร้าง MQTT client ใหม่ทุกครั้ง (Vercel) หรือใช้ persistent (Local)"""
    if USE_MQTT:
        client = mqtt.Client(client_id=NETPIE_CLIENT_ID, protocol=mqtt.MQTTv311)
        client.username_pw_set(NETPIE_TOKEN, NETPIE_SECRET)
        return client
    return None

if USE_MQTT:
    # Local persistent connection
    if not IS_VERCEL:
        mqtt_client = get_mqtt_client()
        mqtt_client.connect(NETPIE_BROKER, 1883, 60)
        mqtt_client.loop_start()
        print("✅ MQTT persistent connection started")
    else:
        # Vercel: we create temporary clients
        print("ℹ️ MQTT mode enabled (temporary connections)")

# ================== Shadow Publish (MQTT or REST) ==================
def publish_shadow(data: dict) -> bool:
    """Publish ไปยัง Shadow โดยเลือกใช้ MQTT หรือ REST ตามสภาพแวดล้อม"""
    if USE_MQTT:
        return _publish_shadow_mqtt(data)
    else:
        return _publish_shadow_rest(data)

def _publish_shadow_mqtt(data: dict) -> bool:
    client = mqtt_client
    if client is None or not client.is_connected():
        # สร้าง temp client (ใช้ใน Vercel)
        client = get_mqtt_client()
        client.connect(NETPIE_BROKER, 1883, 60)
        client.loop_start()
        time.sleep(0.5)  # ให้ connection settle
        temp_client = True
    else:
        temp_client = False

    topic = "@shadow/data/update"
    payload = json.dumps({"data": data})
    try:
        result = client.publish(topic, payload, qos=1)
        ok = result.rc == mqtt.MQTT_ERR_SUCCESS
        if ok:
            print(f"Shadow MQTT published: {data}")
        else:
            print(f"Shadow MQTT failed: {result.rc}")
    except Exception as e:
        ok = False
        print(f"MQTT exception: {e}")

    if temp_client:
        client.loop_stop()
        client.disconnect()
    return ok

def _publish_shadow_rest(data: dict) -> bool:
    url = "https://api.netpie.io/v2/device/shadow/data"
    headers = {
        "Authorization": f"Bearer {NETPIE_TOKEN}",
        "Content-Type": "application/json"
    }
    try:
        resp = requests.put(url, headers=headers, json={"data": data}, timeout=10)
        if resp.status_code == 200:
            print(f"Shadow REST published: {data}")
            return True
        else:
            print(f"Shadow REST failed: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"Shadow REST exception: {e}")
        return False

# ================== LINE Setup ==================
line_bot_api = None
handler = None

if LINE_CHANNEL_TOKEN:
    line_bot_api = LineBotApi(LINE_CHANNEL_TOKEN)
    if LINE_CHANNEL_SECRET:
        handler = WebhookHandler(LINE_CHANNEL_SECRET)
    try:
        bot_info = line_bot_api.get_bot_info()
        print(f"✅ LINE Bot ready: {bot_info.display_name}")
    except Exception as e:
        print(f"❌ LINE Bot init failed: {e}")
        line_bot_api = None

def push_line_message(text: str, user_id: str = None):
    uid = user_id or LINE_USER_ID
    if not uid or not line_bot_api:
        return False
    try:
        line_bot_api.push_message(uid, TextSendMessage(text=text))
        print(f"LINE pushed to {uid}: {text}")
        return True
    except Exception as e:
        print(f"LINE push error: {e}")
        return False

# ================== MongoDB ==================
mongo_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where() if "mongodb+srv" in MONGO_URI else None)
mongo_db = mongo_client["plc_db"]
mongo_collection = mongo_db["test_data"]

def test_mongo_connection():
    try:
        mongo_client.admin.command('ping')
        print("✅ Connected to MongoDB")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        return False

# ================== Command Processor ==================
def process_command(text: str, user_id: str = "unknown") -> str:
    trimmed = text.strip()
    print(f"📩 Command from {user_id}: '{trimmed}'")

    if trimmed.startswith("shadow "):
        json_str = trimmed[len("shadow "):].strip()
        try:
            data = json.loads(json_str)
            ok = publish_shadow(data)
            if ok:
                return f"✅ Shadow updated with: {json.dumps(data)}"
            else:
                return "❌ Shadow update failed"
        except json.JSONDecodeError:
            return "❌ JSON format invalid. Usage: shadow {\"temp\":30}"

    elif trimmed == "mongo":
        docs = list(mongo_collection.find().sort("_id", -1).limit(1))
        if docs:
            doc = docs[0]
            doc["_id"] = str(doc["_id"])
            return f"📄 Latest data: {json.dumps(doc, default=str)}"
        return "📭 No data in MongoDB"

    elif trimmed == "help":
        return (
            "Commands:\n"
            "shadow {json} - update shadow\n"
            "mongo - latest data\n"
            "help - this message"
        )
    else:
        return f"Unknown command: '{trimmed}'. Type 'help' for list."

# ================== FastAPI ==================
app = FastAPI(title="IoT Starter", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup():
    test_mongo_connection()

@app.get("/")
def root():
    return {"message": "IoT Gateway running"}

@app.post("/test/line")
async def test_line(body: dict = Body(...)):
    message = body.get("message", "Hello")
    user_id = body.get("user_id")
    ok = push_line_message(message, user_id)
    return {"sent": ok}

@app.post("/test/shadow")
async def test_shadow(body: dict = Body(...)):
    ok = publish_shadow(body)
    return {"published": ok}

@app.post("/test/mongo")
async def test_mongo_insert(data: dict = Body(...)):
    result = mongo_collection.insert_one(data)
    return {"inserted_id": str(result.inserted_id)}

@app.get("/test/mongo")
async def test_mongo_find():
    docs = list(mongo_collection.find().limit(20))
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return {"count": len(docs), "data": docs}

# ================== LINE Webhook ==================
@app.post("/line/callback")
async def line_callback(request: Request):
    if not handler:
        raise HTTPException(status_code=500, detail="LINE bot not configured")
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"

if handler:
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        user_id = event.source.user_id
        text = event.message.text
        reply = process_command(text, user_id)

        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply)
            )
            print(f"Replied: {reply}")
        except Exception as e:
            print(f"Reply error: {e}")

        if LINE_USER_ID and LINE_USER_ID != user_id:
            push_line_message(f"🛠️ {reply}")

@app.post("/dev/line")
async def dev_line(body: dict = Body(...)):
    events = body.get("events", [])
    for event in events:
        if event.get("type") == "message" and event.get("message", {}).get("type") == "text":
            text = event["message"]["text"]
            reply_text = process_command(text, "dev-user")
            push_line_message(reply_text)
    return {"status": "processed"}