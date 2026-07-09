from fastapi import APIRouter, HTTPException, Body
from linebot.models import TextSendMessage
from services.line_service import line_bot_api, _simulation_state_ref, LINE_USER_ID
from services.mqtt_service import mqtt_input_buffer

router = APIRouter(prefix="/line", tags=["LINE"])

@router.post("/callback")
async def line_callback(body: dict = Body(...)):
    try:
        events = body.get("events", [])
        for event in events:
            if event.get("type") == "message" and event.get("message", {}).get("type") == "text":
                text = event["message"]["text"].strip().lower()
                user_id = event["source"].get("userId", "unknown")
                reply_token = event.get("replyToken")

                # Logic ตอบกลับ
                if not _simulation_state_ref or not _simulation_state_ref.get("project"):
                    reply_text = "No project loaded."
                elif text == "start":
                    mqtt_input_buffer["start_btn"] = True
                    reply_text = "▶️ Start button pressed"
                elif text == "stop":
                    mqtt_input_buffer["stop_btn"] = False
                    reply_text = "⏹ Stop button pressed"
                else:
                    reply_text = "Send 'start' or 'stop' to control"

                # --- 1️⃣ ลอง Reply ผ่าน replyToken ก่อน (ถ้ามีของจริงจะตอบในแชท) ---
                if line_bot_api and reply_token:
                    try:
                        line_bot_api.reply_message(reply_token, TextSendMessage(text=reply_text))
                        print(f"Replied to {user_id}: {reply_text}")
                    except Exception as e:
                        print(f"Reply error: {e}")

                # --- 2️⃣ Push ข้อความตรงไปที่คุณ (เพื่อการทดสอบ) ---
                if line_bot_api and LINE_USER_ID:
                    try:
                        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=f"🛠️ {reply_text}"))
                        print(f"Pushed to {LINE_USER_ID}: {reply_text}")
                    except Exception as e:
                        print(f"Push error: {e}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return "OK"