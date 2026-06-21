import os
import certifi
import numpy as np  # เพิ่ม numpy สำหรับคำนวณสมการ exponential
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
from bson.objectid import ObjectId

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