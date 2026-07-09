import certifi
from pymongo import MongoClient
from datetime import datetime
from config.settings import MONGO_URI
from bson.objectid import ObjectId   # ← import ObjectId


client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['plc_db']                   # ชื่อ database
events_collection = db['plc_events']
users_collection = db['users']          # จากของเดิม

def check_connection():
    try:
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")

def log_event_sync(project: str, var: str, value: str, direction: str):
    """บันทึก PLC event (thread‑safe)"""
    try:
        events_collection.insert_one({
            "timestamp": datetime.utcnow(),
            "project_name": project,
            "variable_name": var,
            "value": value,
            "direction": direction
        })
    except Exception as e:
        print(f"MongoDB log error: {e}")
        
        
projects_collection = db['projects']

def save_project(project_dict: dict):
    """บันทึกโปรเจกต์ลง MongoDB และคืนค่า _id"""
    result = projects_collection.update_one(
        {"project": project_dict["project"]},  # ใช้ชื่อเป็น unique key (หรือจะใช้ _id อย่างเดียวก็ได้)
        {"$set": {"data": project_dict, "updated_at": datetime.utcnow()}},
        upsert=True
    )
    # ดึง _id ของเอกสาร (หาโดย project name)
    doc = projects_collection.find_one({"project": project_dict["project"]})
    return str(doc["_id"]) if doc else None

def get_project_by_id(project_id: str):
    """ดึงโปรเจกต์จาก DB ด้วย ObjectId string"""
    try:
        doc = projects_collection.find_one({"_id": ObjectId(project_id)})  # แปลง str -> ObjectId
        return doc["data"] if doc else None
    except:
        return None

def list_saved_projects():
    """คืนค่ารายการโปรเจกต์พร้อม id"""
    projects = []
    for doc in projects_collection.find({}, {"project": 1, "updated_at": 1}):
        projects.append({
            "id": str(doc["_id"]),
            "project": doc["project"],
            "updated_at": doc["updated_at"].isoformat() if "updated_at" in doc else None
        })
    return projects

def get_latest_project():
    """ดึงโปรเจกต์ล่าสุด (ตาม updated_at)"""
    doc = projects_collection.find_one(sort=[("updated_at", -1)])
    return doc["data"] if doc else None