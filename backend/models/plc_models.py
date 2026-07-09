from pydantic import BaseModel
from typing import Any, Optional, List, Dict

class VariableDef(BaseModel):
    type: str = "BOOL"
    direction: str   # input, output, memory
    initial: Any = None

class LadderElement(BaseModel):
    type: str
    var: Optional[str] = None
    normally: Optional[str] = "open"    # open / closed
    timerType: Optional[str] = "TON"
    preset: Optional[int] = 1000
    set_reset: Optional[str] = None     # SET / RESET

class Rung(BaseModel):
    elements: List[LadderElement]

class ProjectLoad(BaseModel):
    project: str
    scan_time_ms: int = 100
    rungs: List[Rung]
    variables: Dict[str, VariableDef]

class ControlInput(BaseModel):
    var: str
    value: Any

class ShadowData(BaseModel):
    pass

class UserCreate(BaseModel):
    name: str
    email: str

# ====== เพิ่ม SimulationRequest (ใช้สำหรับ Universal Simulation) ======
class SimulationRequest(BaseModel):
    return_pipeline: Optional[bool] = False
    state_vars: List[str] = []
    state_derivatives: List[str] = []
    targets: List[str] = []
    params: Dict[str, float] = {}
    equations: List[str] = []
    intermediates: Dict[str, str] = {}
    conditions: Dict[str, Dict[str, str]] = {}
    z0: List[float] = []
    t_end: float = 3.0
    steps: int = 300
