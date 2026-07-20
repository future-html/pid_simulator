import json
import asyncio
from datetime import datetime
from utils import build_motor_flex
from services.mongo import mongo_collection
from services.mqtt import publish_shadow
from services.modbus import write_modbus_coil_async
from services.line import push_line_message, push_flex_message
from config import config

# ฟังก์ชันสำหรับ MQTT Subscriber Callback
def on_modbus_data_received(data: dict):
    """ตัวอย่างการแจ้งเตือน เมื่อมีข้อมูลมา"""
    modbus_data = data.get("data", {})
    level = modbus_data.get("level")
    
    if level is not None and level > 80:
        push_line_message(f"⚠️ ระดับน้ำสูงเกิน 80! ค่าปัจจุบัน: {level}")

async def process_command(text: str, user_id: str = "unknown") -> str:
    trimmed = text.strip()
    
    if trimmed.startswith("shadow "):
        json_str = trimmed[len("shadow "):].strip()
        try:
            data = json.loads(json_str)
            if publish_shadow(data):
                push_line_message(f"📣 Shadow updated")
                return "✅ Shadow updated"
            return "❌ Shadow update failed"
        except json.JSONDecodeError:
            return "❌ Invalid JSON"

    elif trimmed == "start":
        success = publish_shadow({config.MOTOR_VAR: True})
        modbus_ok = await write_modbus_coil_async(config.OPENPLC_COIL_ADDRESS, True)
        
        if success:
            mongo_collection.insert_one({
                "timestamp": datetime.utcnow(), "command": "start",
                "user": user_id, "project": config.PROJECT_NAME, "value": True
            })
            flex = build_motor_flex(True)
            push_flex_message("Motor ON", flex)
            return f"✅ เปิดมอเตอร์ (Modbus: {'OK' if modbus_ok else 'Failed'})"
        return "❌ Start failed"

    elif trimmed == "stop":
        success = publish_shadow({config.MOTOR_VAR: False})
        modbus_ok = await write_modbus_coil_async(config.OPENPLC_COIL_ADDRESS, False)
        
        if success:
            mongo_collection.insert_one({
                "timestamp": datetime.utcnow(), "command": "stop",
                "user": user_id, "project": config.PROJECT_NAME, "value": False
            })
            flex = build_motor_flex(False)
            push_flex_message("Motor OFF", flex)
            return f"✅ ปิดมอเตอร์ (Modbus: {'OK' if modbus_ok else 'Failed'})"
        return "❌ Stop failed"
        
    elif trimmed == "mongo":
        docs = list(mongo_collection.find().sort("_id", -1).limit(1))
        if docs:
            doc = docs[0]
            doc["_id"] = str(doc["_id"])
            return f"📄 Latest: {json.dumps(doc, default=str)}"
        return "📭 No data"

    elif trimmed == "help":
        return "Commands: shadow {json}, start, stop, mongo, help"
    else:
        return f"Unknown '{trimmed}'. Type 'help'."
