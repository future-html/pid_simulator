import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import Services
from services.mqtt import start_mqtt_subscriber
from services.mongo import mongo_client
from processors import on_modbus_data_received
from config import config
from controllers import register_routers

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Logic
    print("🚀 Starting IoT Gateway...")
    if not config.IS_VERCEL:
        global mqtt_sub_client
        mqtt_sub_client = start_mqtt_subscriber(on_modbus_data_received)
        print("✅ MQTT Subscriber started.")
    yield
    # Shutdown Logic
    if mqtt_sub_client:
        mqtt_sub_client.loop_stop()
        mqtt_sub_client.disconnect()
    if mongo_client:
        mongo_client.close()
    print("🛑 Shutting down...")

app = FastAPI(title="IoT Starter Clean", version="4.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Register all controllers
register_routers(app)