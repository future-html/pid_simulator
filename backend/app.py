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
from scipy.integrate import solve_ivp
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr

# --- Corrected MQTT Configuration (NETPIE) ---
NETPIE_CLIENT_ID = "427e0ae3-fd74-471a-8cc6-3f4dfc7d3641"   
NETPIE_TOKEN = "W8xAzJNmSQAD3DnMZk9kU4DQAC3hksvs"           
NETPIE_SECRET = "xq79QfBmDBYQ4ni3fnoXVwjfvfy3k2mg"
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

@app.route('/api/simulate', methods=['POST'])
def simulate_abs():
    """
    Endpoint สำหรับคำนวณสมการ ABS แบบ Dynamic ผ่าน POST Method
    รับค่าพารามิเตอร์จาก JSON Body จากหน้าบ้าน (React)
    """
    try:
        # 1. ดึงข้อมูล JSON จาก Body ของ POST Request
        data = request.get_json() or {}

        # 2. รับค่าพารามิเตอร์จาก JSON (ถ้าไม่มีการส่งมา จะใช้ค่า Default ด้านหลัง)
        mass = float(data.get('mass', 250.0))       # น้ำหนักตัวรถ (kg)
        Tb_max = float(data.get('torque', 1200.0))   # แรงเบรคสูงสุด (Nm)
        v_init = float(data.get('v_init', 30.0))    # ความเร็วเริ่มต้น (m/s)

        # 3. ตั้งค่าโครงสร้างเชิงตัวเลข (Discrete Simulation Settings)
        dt = 0.01          # ขนาดของ Step (10ms ต่อรอบ กำลังดีสำหรับกราฟเว็บ)
        t_max = 3.0        # จำลองเหตุการณ์สูงสุด 3 วินาที
        n_steps = int(t_max / dt)

        # 4. พารามิเตอร์คงที่ของโมเดล ABS
        J = 1.0            # ความเฉื่อยของล้อ (kg*m^2)
        R = 0.32           # รัศมีล้อ (m)
        g = 9.81           # แรงโน้มถ่วง
        FN = mass * g      # แรงกดแนวตั้ง
        
        # Burckhardt Friction Constants
        c1, c2, c3, c4 = 1.2801, -23.99, 0.52, 0.03

        # 5. สถานะเริ่มต้น (Initial States)
        Vx = v_init
        omega = v_init / R
        
        chart_data = []

        # 6. Simulation Loop (Discrete Math Engine)
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



@app.route('/api/simulate/2dof', methods=['POST'])
def simulate_2dof():
    try:
        # 1. ดึงข้อมูล JSON จาก Body ของ Request
        data = request.get_json() or {}

        # 2. นิยามตัวแปรเชิงสัญลักษณ์ (Symbols) รอไว้สำหรับ SymPy
        m1, m2, k1, k2, c1, c2, F1, F2 = sp.symbols('m1 m2 k1 k2 c1 c2 F1 F2')
        x1, x2, dx1, dx2, ddx1, ddx2 = sp.symbols('x1 x2 dx1 dx2 ddx1 ddx2')

        # 3. รับ String สมการจากหน้าบ้าน (กำหนดแบบรูปสมการ LHS = 0)
        # ถ้าหน้าบ้านไม่ได้ส่งมา จะใช้สมการมาตรฐานของระบบ 2DOF สปริง-แดมเปอร์คู่
        default_eq1 = "m1*ddx1 + (c1 + c2)*dx1 - c2*dx2 + (k1 + k2)*x1 - k2*x2 - F1"
        default_eq2 = "m2*ddx2 - c2*dx1 + c2*dx2 - k2*x1 + k2*x2 - F2"

        eq1_str = data.get('eq1', default_eq1)
        eq2_str = data.get('eq2', default_eq2)

        # แปลงจาก String ไปเป็น Object นิพจน์คณิตศาสตร์ของ SymPy
        eq1_expr = parse_expr(eq1_str)
        eq2_expr = parse_expr(eq2_str)

        # 4. สั่งให้ SymPy แก้ระบบสมการเพื่อหาแง่มุมของความเร่ง (ddx1, ddx2) ออกมาโดยอัตโนมัติ
        # (มันจะทำหน้าที่ย้ายข้างสมการจัดรูปยุ่งๆ ให้เราเอง)
        solved_system = sp.solve([eq1_expr, eq2_expr], (ddx1, ddx2))
        
        if not solved_system:
            return jsonify({"error": "SymPy ไม่สามารถแก้หาค่า ddx1 และ ddx2 จากสมการที่ส่งมาได้"}), 400
            
        ddx1_symbolic = solved_system[ddx1]
        ddx2_symbolic = solved_system[ddx2]

        # 5. เตรียมจับคู่ค่าพารามิเตอร์ตัวเลขที่ส่งมาจาก React
        param_subs = {
            m1: float(data.get('m1', 10.0)),
            m2: float(data.get('m2', 5.0)),
            k1: float(data.get('k1', 100.0)),
            k2: float(data.get('k2', 50.0)),
            c1: float(data.get('c1', 5.0)),
            c2: float(data.get('c2', 2.0)),
            F1: float(data.get('F1', 0.0)),
            F2: float(data.get('F2', 0.0))
        }

        # แทนค่าคงที่ตัวเลขลงไปในตัวสมการสัญลักษณ์เพื่อให้คำนวณตอนท้ายได้เร็วขึ้น
        ddx1_numeric_expr = ddx1_symbolic.subs(param_subs)
        ddx2_numeric_expr = ddx2_symbolic.subs(param_subs)

        # 6. ใช้ lambdify แปลงสมการ SymPy ให้กลายเป็นฟังก์ชัน Python ความเร็วสูง (เทียบเท่าฟังก์ชันปกติ)
        # เรียงอาร์กิวเมนต์ตามลำดับสถานะในตัวแปร z = [x1, x2, dx1, dx2]
        func_ddx1 = sp.lambdify((x1, x2, dx1, dx2), ddx1_numeric_expr, 'numpy')
        func_ddx2 = sp.lambdify((x1, x2, dx1, dx2), ddx2_numeric_expr, 'numpy')

        # 7. สร้างฟังก์ชันสำหรับป้อนเข้า Scipy ODE Solver
        def dynamic_system(t, z):
            x1_val, x2_val, dx1_val, dx2_val = z
            
            # เรียกใช้ฟังก์ชันที่ถูกแปลงมาจาก String แบบ Dynamic
            ddx1_val = float(func_ddx1(x1_val, x2_val, dx1_val, dx2_val))
            ddx2_val = float(func_ddx2(x1_val, x2_val, dx1_val, dx2_val))
            
            return [dx1_val, dx2_val, ddx1_val, ddx2_val]

        # 8. ตั้งค่า Initial Conditions และเวลาการรัน
        z0 = [float(val) for val in data.get('z0', [1.0, 0.0, 0.0, 0.0])]
        t_end = float(data.get('t_end', 10.0))
        t_eval = np.linspace(0, t_end, 1000)

        # สั่งรันคำนวณสมการเชิงอนุพันธ์ (ODE)
        sol = solve_ivp(dynamic_system, [0, t_end], z0, t_eval=t_eval, method='RK45')

        # 9. จัดฟอร์แมต Array ข้อมูลเพื่อส่งกลับไปพล็อต Recharts บน React หน้าบ้าน
        chart_data = []
        for i in range(len(sol.t)):
            chart_data.append({
                "time": float(round(sol.t[i], 3)),
                "x1": float(round(sol.y[0][i], 4)),
                "x2": float(round(sol.y[1][i], 4)),
                "v1": float(round(sol.y[2][i], 4)),
                "v2": float(round(sol.y[3][i], 4))
            })

        return jsonify(chart_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

if __name__ == '__main__':
    # เปิดโปรเจกต์ที่พอร์ต 3000 (หรือพอร์ตอื่นๆ ตามที่คุณสะดวก)
    app.run(debug=True, port=3000)