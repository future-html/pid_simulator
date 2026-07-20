from datetime import datetime

def build_motor_flex(status: bool) -> dict:
    return {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🚀 Motor Status",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#ffffff"
                }
            ],
            "backgroundColor": "#27ACB2" if status else "#8C8C8C"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "สถานะมอเตอร์", "weight": "bold", "size": "md", "color": "#555555"},
                {
                    "type": "text",
                    "text": "ON" if status else "OFF",
                    "size": "3xl",
                    "weight": "bold",
                    "color": "#27ACB2" if status else "#8C8C8C"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"เวลา: {datetime.utcnow().strftime('%H:%M:%S')}",
                    "size": "xs",
                    "color": "#aaaaaa"
                }
            ]
        }
    }




def build_system_flex(level: int, system_run: bool, pump_on: bool) -> dict:
    return {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "📊 สถานะระบบอัตโนมัติ",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#ffffff"
                }
            ],
            "backgroundColor": "#27ACB2"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                # แสดงค่าระดับน้ำ
                {
                    "type": "text",
                    "text": f"📏 ระดับน้ำ: {level}",
                    "size": "md",
                    "weight": "bold",
                    "color": "#555555"
                },
                # แสดงสถานะระบบทำงาน (Run)
                {
                    "type": "box",
                    "layout": "baseline",
                    "contents": [
                        {"type": "text", "text": "ระบบทำงาน:", "size": "sm", "color": "#555555"},
                        {
                            "type": "text", 
                            "text": " ✅ ON" if system_run else " ❌ OFF", 
                            "size": "sm", 
                            "color": "#27ACB2" if system_run else "#FF0000"
                        }
                    ]
                },
                # แสดงสถานะปั๊ม (Pump)
                {
                    "type": "box",
                    "layout": "baseline",
                    "contents": [
                        {"type": "text", "text": "ปั๊มทำงาน:", "size": "sm", "color": "#555555"},
                        {
                            "type": "text", 
                            "text": " 🟢 ON" if pump_on else " 🔴 OFF", 
                            "size": "sm", 
                            "color": "#27ACB2" if pump_on else "#FF0000"
                        }
                    ]
                }
            ]
        }
    }