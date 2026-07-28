from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from services.mongo import save_http_data
from models import SensorDataRequest

router = APIRouter()

@router.post("")
async def api_receive_http_data(body: SensorDataRequest):
    document = {
        "device_id": body.device_id,
        "data": body.data,
        "received_at": datetime.now(timezone.utc).isoformat(),
    }
    inserted_id = save_http_data(document)
    if inserted_id:
        return {"status": "success", "message": "Data saved", "id": inserted_id}
    raise HTTPException(500, "Failed to save data")
