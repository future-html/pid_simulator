from fastapi import APIRouter, HTTPException
from services.mqtt import publish_shadow
from models import MqttPublishRequest, MqttPublishResponse

router = APIRouter(tags=["MQTT"])

@router.post(
    "/publish",
    response_model=MqttPublishResponse,
    summary="Publish data to MQTT shadow",
    description="ส่งข้อมูล batch เข้า NETPIE shadow ผ่าน MQTT รองรับหลาย field พร้อมกัน "
                 "เช่น {\"data\": {\"motor_run\": true, \"speed\": 50}}",
)
async def api_publish_mqtt(body: MqttPublishRequest):
    if not body.data:
        raise HTTPException(400, "Field 'data' must not be empty")

    success = publish_shadow(body.data)
    if success:
        return {"status": "success", "message": "Published to shadow", "data": body.data}
    raise HTTPException(500, "MQTT Publish Failed")
