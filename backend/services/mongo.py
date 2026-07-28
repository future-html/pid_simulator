from pymongo import MongoClient
import certifi
from config import config

def get_mongo_client():
    try:
        client = MongoClient(
            config.MONGO_URI, 
            tlsCAFile=certifi.where() if "mongodb+srv" in config.MONGO_URI else None
        )
        client.admin.command('ping')
        print("✅ Connected to MongoDB")
        return client
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        return None

mongo_client = get_mongo_client()

# แก้ไขตรงนี้: เปลี่ยนจาก if mongo_db เป็น if mongo_db is not None
if mongo_client is not None:
    mongo_db = mongo_client["plc_db"]
    mongo_collection = mongo_db["test_data"] if mongo_db is not None else None
    mqtt_collection = mongo_db["mqtt_data"]
    http_collection = mongo_db["http_data"]
    # --- เพิ่มใหม่: เมนูสินค้า (stock) และ order ---
    menu_collection = mongo_db["menu_items"]
    orders_collection = mongo_db["orders"]
else:
    mongo_db = None
    mongo_collection = None
    mqtt_collection = None
    http_collection = None
    menu_collection = None
    orders_collection = None


def save_mqtt_data(payload: dict) -> str | None:
    if mqtt_collection is None:
        print("⚠️ mqtt_collection ไม่พร้อมใช้งาน (Mongo ไม่ได้เชื่อมต่อ)")
        return None
    try:
        result = mqtt_collection.insert_one(payload)
        return str(result.inserted_id)
    except Exception as e:
        print(f"❌ save_mqtt_data error: {e}")
        return None


def save_http_data(payload: dict) -> str | None:
    if http_collection is None:
        print("⚠️ http_collection ไม่พร้อมใช้งาน (Mongo ไม่ได้เชื่อมต่อ)")
        return None
    try:
        result = http_collection.insert_one(payload)
        return str(result.inserted_id)
    except Exception as e:
        print(f"❌ save_http_data error: {e}")
        return None


# --- เมนูสินค้า / stock ---

def save_menu_item(item: dict) -> str | None:
    """เพิ่มเมนูอาหาร/เครื่องดื่มใหม่เข้า stock"""
    if menu_collection is None:
        print("⚠️ menu_collection ไม่พร้อมใช้งาน (Mongo ไม่ได้เชื่อมต่อ)")
        return None
    try:
        result = menu_collection.insert_one(item)
        return str(result.inserted_id)
    except Exception as e:
        print(f"❌ save_menu_item error: {e}")
        return None


def list_menu_items() -> list[dict]:
    """ดึงรายการเมนูทั้งหมด (สำหรับ frontend ใช้แทน hardcoded list)"""
    if menu_collection is None:
        return []
    try:
        items = list(menu_collection.find())
        for item in items:
            item["_id"] = str(item["_id"])
        return items
    except Exception as e:
        print(f"❌ list_menu_items error: {e}")
        return []


def decrement_menu_stock(item_id: str, quantity: int) -> bool:
    """หัก stock ของเมนู หลังมีคำสั่งซื้อสำเร็จ"""
    if menu_collection is None:
        return False
    try:
        from bson import ObjectId
        result = menu_collection.update_one(
            {"_id": ObjectId(item_id)},
            {"$inc": {"stock": -quantity}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"❌ decrement_menu_stock error: {e}")
        return False


# --- Order (คำสั่งซื้อจาก frontend) ---

def save_order(order: dict) -> str | None:
    if orders_collection is None:
        print("⚠️ orders_collection ไม่พร้อมใช้งาน (Mongo ไม่ได้เชื่อมต่อ)")
        return None
    try:
        result = orders_collection.insert_one(order)
        return str(result.inserted_id)
    except Exception as e:
        print(f"❌ save_order error: {e}")
        return None
