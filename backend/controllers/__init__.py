from fastapi import APIRouter

# รวม routers ทั้งหมดเข้าไว้ด้วยกัน
def register_routers(app):
    from .root import router as root_router
    from .modbus import router as modbus_router
    from .line import router as line_router
    from .test import router as test_router

    app.include_router(root_router)
    app.include_router(modbus_router, prefix="/api/modbus")
    app.include_router(line_router)
    app.include_router(test_router)
