from pydantic import BaseModel

class ModbusCoilRequest(BaseModel):
    address: int
    value: bool

class ModbusRegisterRequest(BaseModel):
    address: int
    value: int
