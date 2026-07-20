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
else:
    mongo_db = None
    mongo_collection = None