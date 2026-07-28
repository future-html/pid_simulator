from fastapi import APIRouter
# รวม routers ทั้งหมดเข้าไว้ด้วยกัน
def register_routers(app):
    from .root import router as root_router
    from .modbus import router as modbus_router
    from .line import router as line_router
    from .test import router as test_router
    from .data import router as data_router
    from .menu import router as menu_router
    from .order import router as order_router
    app.include_router(root_router)
    app.include_router(modbus_router, prefix="/api/modbus")
    app.include_router(line_router)
    app.include_router(test_router)
    app.include_router(data_router, prefix="/api/data")
    app.include_router(menu_router, prefix="/api/menu")
    app.include_router(order_router, prefix="/api/order")
