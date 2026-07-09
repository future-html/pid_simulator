from fastapi import APIRouter, HTTPException
from models.plc_models import SimulationRequest, ControlInput
from services.simulation_service import universal_simulate
from services.simulation_engine import simulation_state
from services.mqtt_service import mqtt_input_buffer

# Router สำหรับ Universal Simulation (ODE/PID)
simulate_router = APIRouter(prefix="/api/simulate", tags=["Universal Simulation"])

# Router สำหรับ PLC Simulation (Status & Control)
plc_router = APIRouter(prefix="/simulation", tags=["PLC Simulation"])

# ---- Universal Simulation Endpoint ----
@simulate_router.post("/universal")
async def universal_simulation(request: SimulationRequest):
    try:
        result = universal_simulate(request.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---- PLC Simulation Status ----
@plc_router.get("/status")
async def get_plc_status():
    """ดูสถานะ PLC simulation ปัจจุบัน"""
    return {
        "running": simulation_state["running"],
        "project": simulation_state["project"]["project"] if simulation_state["project"] else None,
        "variables": simulation_state["variables"]
    }

# ---- PLC Simulation Control ----
@plc_router.post("/control")
async def control_plc_input(ctrl: ControlInput):
    """เปลี่ยนค่าตัวแปร input (สำหรับทดสอบ)"""
    if not simulation_state["project"]:
        raise HTTPException(status_code=400, detail="No project loaded")
    var_name = ctrl.var
    var_info = simulation_state["project"]["variables"].get(var_name)
    if not var_info or var_info["direction"] != "input":
        raise HTTPException(status_code=400, detail="Variable not found or not an input")
    mqtt_input_buffer[var_name] = ctrl.value
    return {"status": "ok", "message": f"Set {var_name} = {ctrl.value}"}