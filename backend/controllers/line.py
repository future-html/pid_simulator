import asyncio
from fastapi import APIRouter, Request, HTTPException, Body
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import ApiClient, MessagingApi, ReplyMessageRequest, TextMessage as LineTextMessage

from services.line import configuration, handler, push_line_message, push_flex_message
from processors import process_command
from utils import build_motor_flex, build_system_flex
from config import config

router = APIRouter()

# ---- LINE Webhook ----
@router.post("/line/callback")
async def line_callback(request: Request):
    if not handler:
        raise HTTPException(500, "LINE Bot not configured")
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    try:
        handler.handle(body.decode(), signature)
    except Exception:
        raise HTTPException(400, "Invalid signature")
    return "OK"

if handler:
    @handler.add(MessageEvent, message=TextMessageContent)
    def handle_message(event):
        asyncio.create_task(handle_async_reply(event, event.source.user_id, event.message.text))

    async def handle_async_reply(event, user_id, text):
        reply = await process_command(text, user_id)
        with ApiClient(configuration) as api:
            MessagingApi(api).reply_message(
                ReplyMessageRequest(reply_token=event.reply_token, messages=[LineTextMessage(text=reply)])
            )

# ---- Test LINE ----
@router.post("/test/line")
async def test_line(body: dict = Body(...)):
    message = body.get("message", "Hello from IoT Gateway")
    user_id = body.get("user_id")
    ok = push_line_message(message, user_id)
    return {"sent": ok, "message": message}

@router.post("/test/flex")
async def test_flex(body: dict = Body(...)):
    status = body.get("status", True)
    user_id = body.get("user_id")
    alt_text = body.get("alt_text", "Motor Status Update")
    flex_dict = build_motor_flex(status)
    ok = push_flex_message(alt_text, flex_dict, user_id)
    return {"sent": ok, "status": status, "alt_text": alt_text}

@router.post("/test/flex/system")
async def test_flex_system(body: dict = Body(...)):
    level = body.get("level", 0)
    system_run = body.get("system_run", False)
    pump_on = body.get("pump_on", False)
    user_id = body.get("user_id")
    alt_text = body.get("alt_text", "อัปเดตสถานะระบบ")
    flex_dict = build_system_flex(level, system_run, pump_on)
    ok = push_flex_message(alt_text, flex_dict, user_id)
    return {"sent": ok, "level": level, "system_run": system_run, "pump_on": pump_on}