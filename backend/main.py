from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers import (
    shadow_controller,
    user_controller,
    project_controller,      # <-- เพิ่ม
    line_controller          # <-- เพิ่ม
)
from controllers.simulation_controller import simulate_router, plc_router
from services.database import check_connection, get_latest_project
from services.mqtt_service import connect_mqtt, subscribe_inputs
from services.simulation_engine import simulation_state, start_simulation
from services.line_service import set_simulation_state_ref

app = FastAPI(title="PLC IoT Gateway", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(shadow_controller.router)
app.include_router(user_controller.router)
app.include_router(simulate_router)
app.include_router(plc_router)
app.include_router(project_controller.router)   # <-- เพิ่ม
app.include_router(line_controller.router)      # <-- เพิ่ม

@app.on_event("startup")
async def startup():
    check_connection()
    connect_mqtt()
    set_simulation_state_ref(simulation_state)   # ถ้ายังใช้ LINE เดิม

    # --- โหลดโปรเจกต์ล่าสุดจาก DB ---
    saved = get_latest_project()
    if saved:
        # ตั้งค่า simulation state แบบเดียวกับใน project_controller
        initial_vars = {}
        for var_name, var_info in saved["variables"].items():
            init_val = var_info.get("initial")
            if init_val is None:
                if var_info["type"] == "BOOL":
                    init_val = False
                elif var_info["type"] == "INT":
                    init_val = 0
                else:
                    init_val = None
            initial_vars[var_name] = init_val

        simulation_state["project"] = saved
        simulation_state["variables"] = initial_vars
        simulation_state["timers"] = {}
        simulation_state["previous_outputs"] = {
            var: initial_vars[var]
            for var, info in saved["variables"].items()
            if info["direction"] == "output"
        }
        subscribe_inputs(saved["project"], saved["variables"])
        start_simulation()
        print(f"✅ Auto-loaded project: {saved['project']}")
    else:
        print("ℹ️ No saved project found in database.")

@app.on_event("shutdown")
async def shutdown():
    from services.simulation_engine import stop_simulation
    stop_simulation()
    from services.database import client
    client.close()

@app.get("/")
async def root():
    return {"message": "PLC IoT Gateway running"}