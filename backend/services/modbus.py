from pymodbus.client import ModbusTcpClient
from config import config
import asyncio

# ใช้ Singleton Pattern เพื่อไม่ให้เชื่อมต่อซ้ำๆ ทุก API Call
_modbus_client = None

def get_modbus_client():
    global _modbus_client
    if _modbus_client is None:
        _modbus_client = ModbusTcpClient(config.OPENPLC_HOST, port=config.OPENPLC_PORT)
    if not _modbus_client.is_socket_open():
        _modbus_client.connect()
    return _modbus_client

def write_modbus_coil_sync(address: int, value: bool) -> bool:
    try:
        client = get_modbus_client()
        response = client.write_coil(address, value)
        return not response.isError()
    except Exception as e:
        print(f"Modbus Coil Error: {e}")
        return False

async def write_modbus_coil_async(address: int, value: bool) -> bool:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, write_modbus_coil_sync, address, value)

def write_modbus_register_sync(address: int, value: int) -> bool:
    try:
        client = get_modbus_client()
        response = client.write_register(address, value)
        return not response.isError()
    except Exception as e:
        print(f"Modbus Register Error: {e}")
        return False

async def write_modbus_register_async(address: int, value: int) -> bool:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, write_modbus_register_sync, address, value)
