# controllers/user_controller.py
from fastapi import APIRouter
from models.plc_models import UserCreate
from services.database import users_collection

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/")
async def get_users():
    users = []
    for user in users_collection.find():
        users.append({
            "id": str(user["_id"]),
            "name": user.get("name", ""),
            "email": user.get("email", "")
        })
    return users

@router.post("/")
async def create_user(user: UserCreate):
    result = users_collection.insert_one(user.dict())
    return {"message": "User created", "id": str(result.inserted_id)}