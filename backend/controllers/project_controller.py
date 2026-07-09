from fastapi import APIRouter, HTTPException
from models.plc_models import ProjectLoad
from services.mqtt_service import subscribe_inputs
from services.simulation_engine import simulation_state, start_simulation, stop_simulation
from services.database import save_project, list_saved_projects, get_project_by_id, get_latest_project
router = APIRouter(prefix="/project", tags=["Project"])

def _apply_project_to_simulation(project_dict: dict):
    """นำโปรเจกต์ (dict) มาใส่ใน simulation engine โดยไม่บันทึก DB (ให้ caller จัดการเอง)"""
    # หยุด simulation เดิม
    stop_simulation()

    # สร้างค่าเริ่มต้นของตัวแปร
    initial_vars = {}
    for var_name, var_info in project_dict["variables"].items():
        init_val = var_info.get("initial")
        if init_val is None:
            if var_info["type"] == "BOOL":
                init_val = False
            elif var_info["type"] == "INT":
                init_val = 0
            else:
                init_val = None
        initial_vars[var_name] = init_val

    # ตั้งค่า state
    simulation_state["project"] = project_dict
    simulation_state["variables"] = initial_vars
    simulation_state["timers"] = {}
    simulation_state["previous_outputs"] = {
        var: initial_vars[var]
        for var, info in project_dict["variables"].items()
        if info["direction"] == "output"
    }

    # Subscribe MQTT input topics
    subscribe_inputs(project_dict["project"], project_dict["variables"])

    # เริ่ม simulation ใหม่
    start_simulation()
    
# --- Endpoint 1: โหลดจาก JSON body (สร้างโปรเจกต์ใหม่) ---
@router.post("/load-project")
async def load_project(proj: ProjectLoad):
    project_dict = proj.dict()
    _apply_project_to_simulation(project_dict)
    
    # บันทึกลง MongoDB และรับ project_id
    project_id = save_project(project_dict)

    return {
        "status": "ok",
        "message": f"Project '{proj.project}' loaded and saved",
        "project_id": project_id
    }

@router.get("/saved")
async def get_saved_projects():
    """รายการโปรเจกต์ที่บันทึกไว้ (พร้อม id)"""
    return list_saved_projects()

@router.get("/saved/{project_id}")
async def get_project_by_id_route(project_id: str):
    """ดูข้อมูลโปรเจกต์ด้วย ID"""
    project_data = get_project_by_id(project_id)
    if not project_data:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_data

@router.get("/saved/{project_name}")
async def get_saved_project(project_name: str):
    """ดึงข้อมูลโปรเจกต์ฉบับเต็มจาก MongoDB โดยใช้ชื่อโปรเจกต์"""
    doc = projects_collection.find_one({"project": project_name})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    return doc["data"]   # ข้อมูลทั้งหมดที่เคยบันทึก

# --- Endpoint 2: โหลดจาก DB โดยใช้ project_id ---
@router.post("/load/{project_id}")
async def load_project_by_id(project_id: str):
    project_data = get_project_by_id(project_id)
    if not project_data:
        raise HTTPException(status_code=404, detail="Project not found")

    _apply_project_to_simulation(project_data)
    # ไม่ต้อง save อีก เพราะข้อมูลอยู่ใน DB แล้ว

    return {
        "status": "ok",
        "message": f"Project '{project_data['project']}' loaded from ID {project_id}",
        "project_id": project_id
    }

