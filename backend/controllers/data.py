from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from services.mongo import save_http_data
from models import SensorDataRequest
    raise HTTPException(500, "Failed to save data")
