import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # NETPIE
    NETPIE_CLIENT_ID = os.getenv("NETPIE_CLIENT_ID", "")
    NETPIE_TOKEN = os.getenv("NETPIE_TOKEN", "")
    NETPIE_SECRET = os.getenv("NETPIE_SECRET", "")
    NETPIE_BROKER = os.getenv("NETPIE_BROKER", "broker.netpie.io")
    
    # LINE
    LINE_CHANNEL_TOKEN = os.getenv("LINE_CHANNEL_TOKEN", "")
    LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
    LINE_USER_ID = os.getenv("LINE_USER_ID", "")
    
    # MONGO
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    
    # MODBUS
    OPENPLC_HOST = os.getenv("OPENPLC_HOST", "127.0.0.1")
    OPENPLC_PORT = int(os.getenv("OPENPLC_PORT", "502"))
    
    # PROJECT
    PROJECT_NAME = os.getenv("PROJECT_NAME", "MotorControl")
    MOTOR_VAR = os.getenv("MOTOR_VAR", "motor_run")
    
    # ENV
    IS_VERCEL = os.getenv("VERCEL", "0") == "1"
    USE_MQTT = True

config = Config()
