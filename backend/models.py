from pydantic import BaseModel

class ModbusCoilRequest(BaseModel):
    address: int
    value: bool

class ModbusRegisterRequest(BaseModel):
    address: int
    value: int

from typing import Any

class SensorDataRequest(BaseModel):
    device_id: str
    data: dict[str, Any]

class MenuItemRequest(BaseModel):
    itemName: str
    cost: float
    stock: int
    image: str = ""
    description: str = ""


class OrderItem(BaseModel):
    itemId: str
    itemName: str
    cost: float
    quantity: int


class OrderRequest(BaseModel):
    items: list[OrderItem]
    payment_method: str
    user_id: str = "unknown"
