import os
import json
from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import paho.mqtt.client as mqtt
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, MessageEvent, TextMessage
from linebot.exceptions import InvalidSignatureError
from dotenv import load_dotenv
import certifi
load_dotenv()

# ================== Configuration ==================
# NETPIE MQTT
NETPIE_CLIENT_ID = os.getenv("NETPIE_CLIENT_ID", "")
NETPIE_TOKEN = os.getenv("NETPIE_TOKEN", "")
NETPIE_SECRET = os.getenv("NETPIE_SECRET", "")
NETPIE_BROKER = os.getenv("NETPIE_BROKER", "broker.netpie.io")

# LINE
LINE_CHANNEL_TOKEN = os.getenv("LINE_CHANNEL_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# ================== MQTT Setup ==================
mqtt_client = mqtt.Client(client_id=NETPIE_CLIENT_ID, protocol=mqtt.MQTTv311)
mqtt_client.username_pw_set(NETPIE_TOKEN, NETPIE_SECRET)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to NETPIE MQTT broker")
    else:
        print(f"❌ MQTT connection failed with code {rc}")

mqtt_client.on_connect = on_connect

def publish_shadow(data: dict):
    """ส่งข้อมูลไปยัง Shadow ของ NETPIE (topic @shadow/data/update)"""
    topic = "@shadow/data/update"
    payload = json.dumps({"data": data})
    if mqtt_client.is_connected():
        result = mqtt_client.publish(topic, payload, qos=1)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"Shadow published: {data}")
            return True
        else:
            print(f"Shadow publish failed: {result.rc}")
            return False
    else:
        print("MQTT not connected")
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
    """ส่ง Push Message ไปยัง LINE user (default ใช้ LINE_USER_ID จาก .env)"""
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

# ================== MongoDB Setup ==================
mongo_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
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

# ================== FastAPI App ==================
app = FastAPI(title="IoT Starter", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup():
    # MQTT
    try:
        mqtt_client.connect(NETPIE_BROKER, 1883, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"MQTT connection error: {e}")
    # MongoDB
    test_mongo_connection()

# ================== Routes ==================
@app.get("/")
def root():
    return {"message": "IoT Gateway running"}

# 1) ส่ง LINE Push Message (POST + JSON body)
@app.post("/test/line")
async def test_line(body: dict = Body(...)):
    message = body.get("message", "Hello")
    user_id = body.get("user_id", None)  # ถ้าไม่ระบุจะใช้ค่าเริ่มต้นจาก .env
    ok = push_line_message(message, user_id)
    return {"sent": ok}

# 2) ส่งข้อมูลขึ้น Shadow (ไม่ใช้ @msg)
@app.post("/test/shadow")
async def test_shadow(body: dict = Body(...)):
    ok = publish_shadow(body)
    return {"published": ok}

# 3) MongoDB
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

# 4) LINE Webhook (สำหรับรับคำสั่งจากผู้ใช้)
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

# LINE message handler (เมื่อมีข้อความเข้า)
if handler:
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        text = event.message.text
        user_id = event.source.user_id
        print(f"📩 Received from {user_id}: {text}")
        # ตอบกลับอัตโนมัติ (สามารถเพิ่ม logic ทีหลัง)
        if line_bot_api:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"คุณพิมพ์ว่า: {text}")
            )