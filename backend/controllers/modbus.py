from fastapi import APIRouter, HTTPException
from services.modbus import write_modbus_coil_async, write_modbus_register_async
from models import ModbusCoilRequest, ModbusRegisterRequest

router = APIRouter()

@router.post("/write_coil")
async def api_write_coil(body: ModbusCoilRequest):
    success = await write_modbus_coil_async(body.address, body.value)
    if success:
        return {"status": "success", "message": f"Write Coil {body.address} -> {body.value}"}
    raise HTTPException(500, "Coil Write Failed")

@router.post("/write_register")
async def api_write_register(body: ModbusRegisterRequest):
    success = await write_modbus_register_async(body.address, body.value)
    if success:
        return {"status": "success", "message": f"Write Register {body.address} -> {body.value}"}
    raise HTTPException(500, "Register Write Failed")
