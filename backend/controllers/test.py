from fastapi import APIRouter, Body
from services.mqtt import publish_shadow
from services.mongo import mongo_collection

router = APIRouter()

@router.post("/test/shadow")
async def test_shadow(body: dict = Body(...)):
    return {"published": publish_shadow(body)}

@router.get("/test/mongo")
async def test_mongo():
    docs = list(mongo_collection.find().limit(5))
    for d in docs:
        d["_id"] = str(d["_id"])
    return {"count": len(docs), "data": docs}
