from fastapi import APIRouter, HTTPException
from services.mqtt import publish_shadow
from models import MqttPublishRequest

router = APIRouter()

@router.post("/publish")
async def api_publish_mqtt(body: MqttPublishRequest):
    if not body.data:
        raise HTTPException(400, "Field 'data' must not be empty")

    success = publish_shadow(body.data)
    if success:
        return {"status": "success", "message": "Published to shadow", "data": body.data}
    raise HTTPException(500, "MQTT Publish Failed")
