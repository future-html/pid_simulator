import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB
MONGO_URI = os.getenv("MONGO_URI")

# NETPIE MQTT
NETPIE_CLIENT_ID = os.getenv("NETPIE_CLIENT_ID", "6826f59b-2946-42d2-9e53-a9a1533b48ae")
NETPIE_TOKEN = os.getenv("NETPIE_TOKEN", "GtwtxGhzzthujCjMCmvnBEjKHp5yiJED")
NETPIE_SECRET = os.getenv("NETPIE_SECRET", "Lk3KRid62qhFgJ4smTJKnPtGVTKgA8RZ")
NETPIE_BROKER = os.getenv("NETPIE_BROKER", "broker.netpie.io")

# LINE Messaging API
LINE_CHANNEL_TOKEN = os.getenv("LINE_CHANNEL_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")