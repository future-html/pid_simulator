import os
import json
import time
import requests
from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi
import paho.mqtt.client as mqtt
from datetime import datetime
from pymodbus.client import ModbusTcpClient
import asyncio
from contextlib import asynccontextmanager

# ================== LINE SDK v3 Imports ==================
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    FlexMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

load_dotenv()

# ================== Configuration ==================
NETPIE_CLIENT_ID = os.getenv("NETPIE_CLIENT_ID", "")
NETPIE_TOKEN = os.getenv("NETPIE_TOKEN", "")
NETPIE_SECRET = os.getenv("NETPIE_SECRET", "")
NETPIE_BROKER = os.getenv("NETPIE_BROKER", "broker.netpie.io")

LINE_CHANNEL_TOKEN = os.getenv("LINE_CHANNEL_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")
LINE_NOTIFY_TOKEN = os.getenv("LINE_NOTIFY_TOKEN", "") # เพิ่มตัวแปรนี้ครับ

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# Environment detection
IS_VERCEL = os.getenv("VERCEL", "0") == "1"
USE_MQTT = True

# ================== OpenPLC Modbus Configuration ==================
OPENPLC_HOST = "127.0.0.1"
OPENPLC_PORT = 502
OPENPLC_COIL_ADDRESS = 3  # Address 2 คือตัวแปร fu (ตามที่คุณตั้งค่า)

# ================== MQTT Client ==================
mqtt_client = None
PROJECT_NAME = "MotorControl"
MOTOR_VAR = "motor_run"

def build_motor_flex(status: bool) -> dict:
    return {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🚀 Motor Status",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#ffffff"
                }
            ],
            "backgroundColor": "#27ACB2" if status else "#8C8C8C"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "สถานะมอเตอร์", "weight": "bold", "size": "md", "color": "#555555"},
                {
                    "type": "text",
                    "text": "ON" if status else "OFF",
                    "size": "3xl",
                    "weight": "bold",
                    "color": "#27ACB2" if status else "#8C8C8C"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"เวลา: {datetime.utcnow().strftime('%H:%M:%S')}",
                    "size": "xs",
                    "color": "#aaaaaa"
                }
            ]
        }
    }

def get_mqtt_client():
    if USE_MQTT:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=NETPIE_CLIENT_ID, protocol=mqtt.MQTTv311)
        client.username_pw_set(NETPIE_TOKEN, NETPIE_SECRET)
        return client
    return None

if USE_MQTT:
    if not IS_VERCEL:
        mqtt_client = get_mqtt_client()
        mqtt_client.connect(NETPIE_BROKER, 1883, 60)
        mqtt_client.loop_start()
        print("✅ MQTT persistent connection started")
    else:
        print("ℹ️ MQTT mode enabled (temporary connections)")

def publish_shadow(data: dict) -> bool:
    if USE_MQTT:
        return _publish_shadow_mqtt(data)
    else:
        return _publish_shadow_rest(data)

def _publish_shadow_mqtt(data: dict) -> bool:
    client = get_mqtt_client()
    if client is None:
        return False

    conn_ok = False
    def on_connect(client, userdata, flags, rc):
        nonlocal conn_ok
        conn_ok = (rc == 0)

    client.on_connect = on_connect
    client.connect(NETPIE_BROKER, 1883, 60)
    client.loop_start()

    timeout = 3
    start = time.time()
    while not conn_ok and (time.time() - start) < timeout:
        time.sleep(0.1)

    if not conn_ok:
        client.loop_stop()
        client.disconnect()
        print("MQTT connection failed")
        return False

    topic = "@shadow/data/update"
    payload = json.dumps({"data": data})
    try:
        result = client.publish(topic, payload, qos=1)
        ok = result.rc == mqtt.MQTT_ERR_SUCCESS
        if ok:
            print(f"Shadow MQTT published: {data}")
        else:
            print(f"Shadow MQTT publish failed: {result.rc}")
    except Exception as e:
        ok = False
        print(f"MQTT exception: {e}")

    client.loop_stop()
    client.disconnect()
    return ok

def _publish_shadow_rest(data: dict) -> bool:
    url = "https://api.netpie.io/v2/device/shadow/data"
    headers = {
        "Authorization": f"Device {NETPIE_CLIENT_ID}:{NETPIE_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"data": data}
    try:
        resp = requests.put(url, json=payload, headers=headers, timeout=10)
        print(f"REST status: {resp.status_code}, body: {resp.text}")
        if resp.status_code == 200:
            print(f"Shadow REST published: {data}")
            return True
        else:
            print(f"Shadow REST failed: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"Shadow REST exception: {e}")
        return False

# ================== LINE Setup (v3) ==================
configuration = None
handler = None

if LINE_CHANNEL_TOKEN:
    configuration = Configuration(access_token=LINE_CHANNEL_TOKEN)
    if LINE_CHANNEL_SECRET:
        handler = WebhookHandler(LINE_CHANNEL_SECRET)
    print("✅ LINE Bot v3 initialized")

# LINE Push Function (v3)
def push_line_message(text: str, user_id: str = None):
    uid = user_id or LINE_USER_ID
    if not uid or not configuration:
        return False
    try:
        with ApiClient(configuration) as api_client:
            line_bot = MessagingApi(api_client)
            line_bot.push_message(
                PushMessageRequest(
                    to=uid,
                    messages=[TextMessage(text=text)]
                )
            )
        print(f"LINE pushed to {uid}: {text}")
        return True
    except Exception as e:
        print(f"LINE push error: {e}")
        return False

def push_flex_message(alt_text: str, flex_dict: dict, user_id: str = None):
    uid = user_id or LINE_USER_ID
    if not uid or not configuration:
        return False
    try:
        with ApiClient(configuration) as api_client:
            line_bot = MessagingApi(api_client)
            line_bot.push_message(
                PushMessageRequest(
                    to=uid,
                    messages=[FlexMessage(alt_text=alt_text, contents=flex_dict)]
                )
            )
        print(f"Flex pushed to {uid}")
        return True
    except Exception as e:
        print(f"Flex push error: {e}")
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

# ================== Modbus ==================
def write_modbus_sync(address: int, value: bool) -> bool:
    client = None
    try:
        client = ModbusTcpClient(OPENPLC_HOST, port=OPENPLC_PORT)
        if not client.connect():
            print(f"❌ ไม่สามารถเชื่อมต่อ OpenPLC ที่ {OPENPLC_HOST}:{OPENPLC_PORT}")
            return False
        
        index = address - 1
        response = client.write_coil(index, value)
        client.close()
        
        if response.isError():
            print(f"❌ Modbus Write Error: {response}")
            return False
            
        print(f"✅ ส่ง Write Coil ไปที่ Address {address} ค่า {value} สำเร็จ")
        return True
    except Exception as e:
        print(f"❌ Modbus Exception: {e}")
        return False

async def write_modbus_async(address: int, value: bool) -> bool:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, write_modbus_sync, address, value)

# ================== Command Processor (Async version) ==================
async def process_command(text: str, user_id: str = "unknown") -> str:
    trimmed = text.strip()
    print(f"📩 Command from {user_id}: '{trimmed}'")

    if trimmed.startswith("shadow "):
        json_str = trimmed[len("shadow "):].strip()
        json_str = " ".join(json_str.split())
        try:
            data = json.loads(json_str)
            ok = publish_shadow(data)
            if ok:
                push_line_message(f"📣 Shadow updated: {json.dumps(data)}")
                return f"✅ Shadow updated with: {json.dumps(data)}"
            else:
                return "❌ Shadow update failed"
        except json.JSONDecodeError:
            return "❌ JSON format invalid. Usage: shadow {\"temp\":30}"

    elif trimmed == "start":
        data = {MOTOR_VAR: True}
        ok = publish_shadow(data)
        
        # 🆕 ส่งคำสั่งไปเปิด OpenPLC Address 2 (fu) ด้วย!
        modbus_ok = await write_modbus_async(OPENPLC_COIL_ADDRESS, True)
        
        if ok:
            mongo_collection.insert_one({
                "timestamp": datetime.utcnow(),
                "command": "start",
                "user": user_id,
                "project": PROJECT_NAME,
                "variable": MOTOR_VAR,
                "value": True
            })
            flex = build_motor_flex(True)
            push_flex_message("Motor ON", flex)
            push_line_message(f"▶️ มอเตอร์เริ่มทำงาน (Project: {PROJECT_NAME})")
            return f"✅ มอเตอร์เริ่มทำงาน (Modbus: {'OK' if modbus_ok else 'Failed'})"
        else:
            return "❌ ไม่สามารถเริ่มมอเตอร์ได้"

    elif trimmed == "stop":
        data = {MOTOR_VAR: False}
        ok = publish_shadow(data)
        
        # 🆕 ส่งคำสั่งไปปิด OpenPLC Address 2 (fu) ด้วย!
        modbus_ok = await write_modbus_async(OPENPLC_COIL_ADDRESS, False)
        
        if ok:
            mongo_collection.insert_one({
                "timestamp": datetime.utcnow(),
                "command": "stop",
                "user": user_id,
                "project": PROJECT_NAME,
                "variable": MOTOR_VAR,
                "value": False
            })
            flex = build_motor_flex(False)
            push_flex_message("Motor OFF", flex)
            push_line_message(f"⏹️ มอเตอร์หยุดทำงาน (Project: {PROJECT_NAME})")
            return f"✅ มอเตอร์หยุดทำงาน (Modbus: {'OK' if modbus_ok else 'Failed'})"
        else:
            return "❌ ไม่สามารถหยุดมอเตอร์ได้"

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
            "start - turn motor ON\n"
            "stop - turn motor OFF\n"
            "mongo - latest data\n"
            "help - this message"
        )
    else:
        return f"Unknown command: '{trimmed}'. Type 'help' for list."

# ================== FastAPI Lifespan & App ==================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    test_mongo_connection()
    yield
    # Shutdown (ถ้ามี)
    # mongo_client.close()

app = FastAPI(title="IoT Starter", version="3.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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
    @handler.add(MessageEvent, message=TextMessageContent)
    def handle_message(event):
        user_id = event.source.user_id
        text = event.message.text
        # ใช้ asyncio.create_task เพื่อรัน async โดยไม่บล็อก Webhook
        asyncio.create_task(process_and_reply(event, user_id, text))

    async def process_and_reply(event, user_id, text):
        reply = await process_command(text, user_id)
        try:
            with ApiClient(configuration) as api_client:
                line_bot = MessagingApi(api_client)
                line_bot.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply)]
                    )
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
            reply_text = await process_command(text, "dev-user")
            push_line_message(reply_text)
    return {"status": "processed"}

@app.post("/auto-status")
async def auto_status():
    # status in real time use cron job for schedule time for notification
    import random
    status = random.choice([True, False])
    flex = build_motor_flex(status)
    push_flex_message("Motor Status Update", flex)
    return {"sent": True, "status": status}

@app.post("/api/modbus/write")
async def api_modbus_write(body: dict = Body(...)):
    """API รับค่าไป Write Coil ยัง OpenPLC โดยตรง"""
    address = body.get("address", OPENPLC_COIL_ADDRESS)
    value = body.get("value", False)
    
    success = await write_modbus_async(int(address), bool(value))
    if success:
        return {"status": "success", "message": f"เขียนค่า {value} ไปที่ Address {address} แล้ว"}
    else:
        raise HTTPException(status_code=500, detail="Modbus Write Failed")