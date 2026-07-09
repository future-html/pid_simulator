from fastapi import APIRouter, HTTPException
import json
from models.plc_models import ShadowData
from services.mqtt_service import publish_shadow

router = APIRouter(prefix="/api/shadow", tags=["Shadow"])

@router.post("/update")
async def update_shadow(data: ShadowData):
    sensor_data = data.dict()
    shadow_payload = {"data": sensor_data}
    payload_string = json.dumps(shadow_payload)
    
    success, attempts = publish_shadow(payload_string)
    if success:
        return {"status": "Shadow updated successfully", "attempts": attempts}
    else:
        raise HTTPException(status_code=503, detail=f"Failed after {attempts} attempts")