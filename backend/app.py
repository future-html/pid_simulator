import os
import certifi
import numpy as np  # เพิ่ม numpy สำหรับคำนวณสมการ exponential
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
from bson.objectid import ObjectId
import json
import paho.mqtt.client as mqtt
from threading import Lock
import time
# --- Corrected MQTT Configuration (NETPIE) ---
NETPIE_CLIENT_ID = "427e0ae3-fd74-471a-8cc6-3f4dfc7d3641"   
NETPIE_TOKEN = "W8xAzJNmSQAD3DnMZk9kU4DQAC3hksvs"           
NETPIE_SECRET = "xq79QfBmDBYQ4ni3fnoXVwjfvfy3k2mg" # <-- You need to add this from NETPIE
NETPIE_BROKER = os.getenv("NETPIE_BROKER", "broker.netpie.io")

mqtt_client = mqtt.Client(client_id=NETPIE_CLIENT_ID, protocol=mqtt.MQTTv311)
# 2. Token goes into username, Secret goes into password
mqtt_client.username_pw_set(NETPIE_TOKEN, NETPIE_SECRET)

# Global lock for thread safety when publishing
mqtt_lock = Lock()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to NETPIE MQTT broker")
    else:
        print(f"❌ Connection failed with code {rc}")

mqtt_client.on_connect = on_connect

# Connect and start the loop in a background thread (non-blocking)
try:
    mqtt_client.connect(NETPIE_BROKER, 1883, 60)
    mqtt_client.loop_start()  # runs in a daemon thread
except Exception as e:
    print(f"❌ MQTT connection error: {e}")
    
    
load_dotenv()

app = Flask(__name__)
CORS(app)

mongo_uri = os.getenv("MONGO_URI")

# เชื่อมต่อ MongoDB พร้อมตรวจสอบใบรับรองความปลอดภัย
client = MongoClient(mongo_uri, tlsCAFile=certifi.where())

try:
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB!")
except ConnectionFailure:
    print("❌ Failed to connect to MongoDB. Check your connection string.")

db = client['sample_mflix']
users_collection = db['users']

@app.route('/api/shadow/update', methods=['POST'])
def update_shadow():
    """
    Updates the NETPIE Device Shadow with automatic retry logic.
    """
    sensor_data = request.get_json()
    if not sensor_data:
        return jsonify({"error": "No data provided"}), 400

    # Wrap it in NETPIE's required structure
    shadow_payload = {"data": sensor_data}
    payload_string = json.dumps(shadow_payload)
    topic = "@shadow/data/update"

    # --- Retry Settings ---
    max_retries = 5       # Stop trying after 5 attempts
    retry_delay = 1.0     # Wait 1 second between attempts
    attempt = 0

    while attempt < max_retries:
        attempt += 1
        
        # 1. If the client isn't connected yet, wait and try again
        if not mqtt_client.is_connected():
            print(f"⚠️ [Attempt {attempt}/{max_retries}] MQTT client offline. Waiting {retry_delay}s...")
            time.sleep(retry_delay)
            continue

        # 2. If connected, attempt to publish
        try:
            with mqtt_lock:
                result = mqtt_client.publish(topic, payload_string, qos=1)
            
            # 3. Check if the broker accepted the request
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                # Optional: Force the code to wait until the broker acknowledges receipt (QoS 1)
                # result.wait_for_publish(timeout=2.0)
                
                print(f"✅ Shadow updated successfully on attempt {attempt}!")
                return jsonify({
                    "status": "Shadow updated successfully",
                    "attempts": attempt,
                    "topic": topic,
                    "payload_sent": shadow_payload
                }), 200
            
            print(f"⚠️ [Attempt {attempt}/{max_retries}] Publish failed with code {result.rc}")
            
        except Exception as e:
            print(f"❌ [Attempt {attempt}/{max_retries}] Error during publish: {e}")
        
        # Wait before the next attempt loop
        time.sleep(retry_delay)

    # If the code reaches here, it means all retries failed
    return jsonify({
        "error": f"Failed to update shadow after {max_retries} attempts. Broker unavailable."
    }), 503

# --- ROUTES สำหรับจัดการ USERS (ของเดิมของคุณ) ---

@app.route('/users', methods=['GET'])
def get_users():
    """Retrieve all users from the database."""
    try:
        users = []
        for user in users_collection.find():
            users.append({
                "id": str(user['_id']), 
                "name": user.get('name', 'No Name Provided'), 
                "email": user.get('email', 'No Email Provided')
            })
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/users', methods=['POST'])
def create_user():
    """Create a new user in the database."""
    data = request.get_json()
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({"error": "Missing name or email"}), 400

    new_user = {
        "name": data['name'],
        "email": data['email']
    }
    
    try:
        result = users_collection.insert_one(new_user)
        return jsonify({
            "message": "User created successfully", 
            "id": str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- ROUTES ใหม่สำหรับระบบ ABS SIMULATION (เพื่อส่งให้ React) ---

@app.route('/api/simulate', methods=['GET'])
def simulate_abs():
    """
    Endpoint สำหรับคำนวณสมการ ABS แบบ Dynamic 
    รองรับ Query Parameters เพื่อปรับเปลี่ยนค่าจากหน้าบ้านได้ เช่น:
    /api/simulate?mass=250&torque=1200&v_init=30
    """
    try:
        # 1. รับค่าพารามิเตอร์จาก React (ถ้าไม่ส่งมาจะใช้ค่า Default ข้างหลัง)
        mass = float(request.args.get('mass', 250.0))       # น้ำหนักตัวรถ (kg)
        Tb_max = float(request.args.get('torque', 1200.0))   # แรงเบรคสูงสุด (Nm)
        v_init = float(request.args.get('v_init', 30.0))    # ความเร็วเริ่มต้น (m/s)

        # 2. ตั้งค่าโครงสร้างเชิงตัวเลข (Discrete Simulation Settings)
        dt = 0.01          # ขนาดของ Step (10ms ต่อรอบ กำลังดีสำหรับกราฟเว็บ)
        t_max = 3.0        # จำลองเหตุการณ์สูงสุด 3 วินาที
        n_steps = int(t_max / dt)

        # 3. พารามิเตอร์คงที่ของโมเดล ABS
        J = 1.0            # ความเฉื่อยของล้อ (kg*m^2)
        R = 0.32           # รัศมีล้อ (m)
        g = 9.81           # แรงโน้มถ่วง
        FN = mass * g      # แรงกดแนวตั้ง
        
        # Burckhardt Friction Constants
        c1, c2, c3, c4 = 1.2801, -23.99, 0.52, 0.03

        # 4. สถานะเริ่มต้น (Initial States)
        Vx = v_init
        omega = v_init / R
        
        chart_data = []

        # 5. Simulation Loop (Discrete Math Engine)
        for i in range(n_steps):
            t = i * dt
            
            # บันทึกสถานะปัจจุบันลงใน Array ที่จะส่งกลับไปให้ Recharts ใน React
            chart_data.append({
                "time": float(round(t, 3)),
                "vx": float(round(Vx, 2)),
                "wr": float(round(omega * R, 2))
            })

            # SAFETY SWITCH: ถ้าความเร็วรถต่ำกว่า 0.5 m/s ถือว่ารถหยุดสนิทแล้ว
            if Vx < 0.5:
                continue

            # คำนวณ Slip Ratio (λ)
            lambda_val = (Vx - omega * R) / Vx
            lambda_val = max(0.0, min(lambda_val, 1.0)) # คุมค่าให้อยู่ในช่วง 0 - 1

            # ABS Controller Logic (Bang-Bang Relay)
            if lambda_val > 0.20:
                Tb = 0.0        # ปล่อยเบรคชั่วคราวเมื่อล้อเริ่มล็อก
            else:
                Tb = Tb_max     # จับเบรคเต็มแรงเมื่อล้อยังยึดเกาะได้อยู่

            # คำนวณสัมประสิทธิ์แรงเสียดทานด้วย Burckhardt Formula
            mu = (c1 * (1.0 - np.exp(c2 * lambda_val)) - c3 * lambda_val) * np.exp(-c4 * Vx)
            
            # คำนวณแรงและทอร์กที่เกิดขึ้นจริง
            Ff = mu * FN
            T_road = Ff * R

            # สมการเชิงอนุพันธ์แปลงเป็น Discrete (Euler Method)
            dVx = -Ff / mass
            domega = (T_road - Tb) / J

            # อัปเดตค่าความเร็วสำหรับรอบถัดไป
            Vx += dVx * dt
            omega += domega * dt
            
            if omega < 0:
                omega = 0.0

        return jsonify(chart_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # เปิดโปรเจกต์ที่พอร์ต 3000 (หรือพอร์ตอื่นๆ ตามที่คุณสะดวก)
    app.run(debug=True, port=3000)