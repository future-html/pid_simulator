from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from config.settings import LINE_CHANNEL_TOKEN, LINE_CHANNEL_SECRET, LINE_USER_ID

line_bot_api = None
handler = None

if LINE_CHANNEL_TOKEN and LINE_CHANNEL_SECRET:
    line_bot_api = LineBotApi(LINE_CHANNEL_TOKEN)
    handler = WebhookHandler(LINE_CHANNEL_SECRET)
    try:
        bot_info = line_bot_api.get_bot_info()
        print(f"✅ LINE Bot connected: {bot_info.display_name} (Bot ID: {bot_info.user_id})")
    except Exception as e:
        print(f"❌ LINE Bot initialization failed: {e}")
        line_bot_api = None
        handler = None
else:
    print("⚠️ LINE credentials missing – Bot disabled")

def send_line_notification(message: str):
    if line_bot_api and LINE_USER_ID:
        try:
            line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))
            print(f"LINE push sent: {message}")
        except Exception as e:
            print(f"LINE push error: {e}")
            
_simulation_state_ref = None

def set_simulation_state_ref(state_ref):
    global _simulation_state_ref
    _simulation_state_ref = state_ref

if handler:
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        text = event.message.text.strip().lower()
        user_id = event.source.user_id
        if LINE_USER_ID and user_id != LINE_USER_ID:
            return
        if not _simulation_state_ref or not _simulation_state_ref.get("project"):
            reply = "No project loaded."
        elif text == "start":
            from services.mqtt_service import mqtt_input_buffer
            mqtt_input_buffer["start_btn"] = True
            reply = "▶️ Start button pressed"
        elif text == "stop":
            from services.mqtt_service import mqtt_input_buffer
            mqtt_input_buffer["stop_btn"] = False
            reply = "⏹ Stop button pressed"
        else:
            reply = "Send 'start' or 'stop' to control"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
