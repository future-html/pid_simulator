from fastapi import APIRouter, HTTPException
from services.mqtt import publish_shadow
from services.mongo import save_order, decrement_menu_stock
from models import OrderRequest

router = APIRouter()

@router.post("")
async def api_checkout(body: OrderRequest):
    """
    รับ order จาก frontend (เดิมยิงตรงไป NETPIE จาก client ทำให้ token หลุด)
    ตอนนี้ยิงผ่าน publish_shadow() ซึ่งจะเลือกใช้ MQTT หรือ HTTP REST
    โดยอัตโนมัติตาม config.USE_MQTT ที่ตั้งไว้ใน config.py
    """
    number_payload = " ".join(item.itemName for item in body.items)

    published = publish_shadow({"number": number_payload})
    if not published:
        raise HTTPException(500, "Failed to publish to NETPIE shadow")

    # หัก stock ของแต่ละเมนูตามจำนวนที่สั่งจริง
    for item in body.items:
        decrement_menu_stock(item.itemId, item.quantity)

    # บันทึก order ไว้เป็นประวัติ
    order_doc = {
        "items": [item.model_dump() for item in body.items],
        "payment_method": body.payment_method,
        "user_id": body.user_id,
        "total": sum(item.cost * item.quantity for item in body.items),
    }
    order_id = save_order(order_doc)

    return {"status": "success", "message": "Order placed", "order_id": order_id}
