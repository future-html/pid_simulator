from fastapi import APIRouter, HTTPException
from services.mongo import save_menu_item, list_menu_items
from models import MenuItemRequest

router = APIRouter()

@router.post("")
async def api_add_menu_item(body: MenuItemRequest):
    """เพิ่มเมนูอาหาร/เครื่องดื่มใหม่เข้า stock"""
    inserted_id = save_menu_item(body.model_dump())
    if inserted_id:
        return {"status": "success", "message": "Menu item added", "id": inserted_id}
    raise HTTPException(500, "Failed to add menu item")

@router.get("")
async def api_list_menu_items():
    """ดึงรายการเมนูทั้งหมด สำหรับ frontend เอาไปแสดงแทน hardcoded list"""
    items = list_menu_items()
    return {"status": "success", "items": items}
