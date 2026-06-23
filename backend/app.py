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


@app.route('/api/analyze/control', methods=['POST'])
def analyze_control():
    try:
        data = request.get_json() or {}
        
        state_vars_names = data.get('state_vars', [])       # Ex: ["x", "dx"]
        state_deriv_names = data.get('state_derivatives', []) 
        target_names = data.get('targets', [])               # Ex: ["ddx"]
        equations_strs = data.get('equations', [])          
        user_params = data.get('params', {})                
        
        # คีย์สำคัญสำหรับการวิเคราะห์ระบบควบคุม
        input_var_name = data.get('input_var')              # ตัวแปรควบคุมหลัก Ex: "F" หรือ "tau"
        output_var_name = data.get('output_var')            # ตัวแปรผลลัพธ์ที่สนใจ Ex: "x" หรือ "r"

        if not input_var_name or not output_var_name:
            return jsonify({"error": "กรุณาระบุ input_var และ output_var สำหรับการวิเคราะห์"}), 400

        # 1. สร้าง Base Symbols และแก้ระบบสมการหาพจน์อนุพันธ์สูงสุด
        sym_dict = {}
        all_names = state_vars_names + state_deriv_names + target_names + list(user_params.keys()) + [input_var_name]
        for name in all_names:
            if name not in sym_dict:
                sym_dict[name] = sp.Symbol(name)

        parsed_eqs = [parse_expr(eq, local_dict=sym_dict) for eq in equations_strs]
        target_symbols = [sym_dict[name] for name in target_names]
        
        solved = sp.solve(parsed_eqs, target_symbols)
        if not solved:
            return jsonify({"error": "ไม่สามารถแก้สมการเพื่อหาความสัมพันธ์เชิงสัญลักษณ์ได้"}), 400

        # 2. จัดรูปแบบสมการอนุพันธ์อันดับหนึ่ง: dx/dt = f(x, u)
        # แมปชื่อตัวแปรอนุพันธ์กับพจน์สมสัญญลักษณ์ที่ย้ายข้างแล้ว
        f_exprs = []
        for deriv_name in state_deriv_names:
            if deriv_name in state_vars_names:
                # เคสทั่วไปเช่น dx = dx (เป็นตัวแปรสถานะอยู่แล้ว)
                f_exprs.append(sym_dict[deriv_name])
            elif deriv_name in target_names:
                # เคสที่เป็นพจน์สูงสุดที่เพิ่งย้ายข้างมา เช่น ddx = (-c*dx - k*x + F)/m
                expr = solved[sym_dict[deriv_name]] if isinstance(solved, dict) else solved[0]
                f_exprs.append(expr)

        # 3. 🔥 DYNAMIC LINEARIZATION (หาเมทริกซ์ State-Space A และ B ด้วย Jacobian)
        state_vector = [sym_dict[name] for name in state_vars_names]
        input_symbol = sym_dict[input_var_name]
        
        # หาอนุพันธ์ย่อยเทียบกับ State (Matrix A) และเทียบกับ Input (Matrix B)
        A_jacobian = sp.Matrix(f_exprs).jacobian(state_vector)
        B_jacobian = sp.Matrix(f_exprs).jacobian([input_symbol])

        # 4. แทนค่าพารามิเตอร์คงที่และจุดสมดุล (Equilibrium Point) ให้กลายเป็นตัวเลข
        # สมมุติให้ระบบคำนวณรอบจุดทำงานเริ่มต้นที่ z0 = 0.0 และ u = 0.0
        equilibrium_subs = {sym_dict[name]: 0.0 for name in state_vars_names}
        equilibrium_subs[input_symbol] = 0.0
        param_subs = {sym_dict[k]: float(v) for k, v in user_params.items() if k in sym_dict}
        
        # รวมการแทนค่าทั้งหมด
        final_subs = {**param_subs, **equilibrium_subs}
        
        A_num = np.array(A_jacobian.subs(final_subs)).astype(np.float64)
        B_num = np.array(B_jacobian.subs(final_subs)).astype(np.float64)

        # สร้างเมทริกซ์ C และ D จากตัวแปรผลลัพธ์ (Output) ที่เลือก
        C_num = np.zeros((1, len(state_vars_names)))
        if output_var_name in state_vars_names:
            C_num[0, state_vars_names.index(output_var_name)] = 1.0
        D_num = np.zeros((1, 1))

        # แปลงโครงสร้าง State-Space เป็นวัตถุระบบของ SciPy
        sys_ss = signal.StateSpace(A_num, B_num, C_num, D_num)

        # 5. 📈 คำนวณข้อมูล BODE PLOT
        # กำหนดช่วงความถี่แบบ Logarithmic (10^-2 ถึง 10^3 rad/s) ทั้งหมด 200 จุด
        w_space = np.logspace(-2, 3, 200)
        w, mag, phase = signal.bode(sys_ss, w=w_space)
        
        bode_data = []
        for i in range(len(w)):
            bode_data.append({
                "frequency": float(w[i]),
                "magnitude": float(mag[i]),
                "phase": float(phase[i])
            })

        # 6. 🎯 คำนวณข้อมูล ROOT LOCUS (พิกัดการเดินของรากเมื่อ Gain K เปลี่ยนแปลง)
        # วนลูปเปลี่ยนค่า Gain ตั้งแต่ 0 ถึงพิกัดสูงสุด
        gains = np.logspace(-1, 3, 150) # ลิสต์ค่า Gain K ตั้งแต่ 0.1 ถึง 1000
        root_locus_data = []
        
        for k_gain in gains:
            # ในระบบป้อนกลับ (Closed-Loop) ขั้วของระบบ (Poles) คือค่า Eigenvalues ของเมทริกซ์ (A - K*B*C)
            closed_loop_A = A_num - k_gain * (B_num @ C_num)
            poles = np.linalg.eigvals(closed_loop_A)
            
            for p in poles:
                root_locus_data.append({
                    "gain": float(k_gain),
                    "real": float(np.real(p)),
                    "imag": float(np.imag(p))
                })

        # 7. คืนค่าผลลัพธ์วิเคราะห์คู่คู่ส่งกลับให้ React
        return jsonify({
            "bode_plot": bode_data,
            "root_locus": root_locus_data,
            "matrices": {
                "A": A_num.tolist(),
                "B": B_num.tolist(),
                "C": C_num.tolist()
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/simulate/universal', methods=['POST'])
def universal_simulate():
    try:
        data = request.get_json() or {}
        
        state_vars_names = data.get('state_vars', [])       
        state_deriv_names = data.get('state_derivatives', []) 
        target_names = data.get('targets', [])               
        user_params = data.get('params', {})                
        equations_strs = data.get('equations', [])          

        # 1. สร้าง Base Symbols สำหรับตัวแปรพื้นฐานและพารามิเตอร์
        sym_dict = {'t': sp.Symbol('t')}
        all_possible_names = (
            state_vars_names + state_deriv_names + target_names + list(user_params.keys())
        )
        for name in all_possible_names:
            if name not in sym_dict:
                sym_dict[name] = sp.Symbol(name)

        # 2. ➕ ปลั๊กอินระบบ INTERMEDIATES (สมการตัวแปรตัวกลางทางฟิสิกส์)
        # รับค่าเช่น {"lambda_val": "(vx - omega * R) / vx"}
        intermediates_data = data.get('intermediates', {})
        for var_name, expr_str in intermediates_data.items():
            if var_name not in sym_dict:
                sym_dict[var_name] = sp.Symbol(var_name)
                
        # แปลงโครงสร้างสมการตัวกลางเก็บไว้
        inter_exprs = {k: parse_expr(v, local_dict=sym_dict) for k, v in intermediates_data.items()}

        # 3. 🧠 ปลั๊กอินระบบ CONDITIONS (ไอเดียของคุณแปลงเป็น sp.Piecewise)
        # รับค่าเช่น {"Tb": {"lambda_val > 0.20": "0.0", "default": "torque"}}
        conditions_data = data.get('conditions', {})
        conditional_expressions = {}
        
        for var_name, cond_map in conditions_data.items():
            if var_name not in sym_dict:
                sym_dict[var_name] = sp.Symbol(var_name)
                
            pairs = []
            for cond_str, val_str in cond_map.items():
                # แปลงค่าผลลัพธ์ (Value) เช่น "0.0" หรือ "torque"
                val_expr = parse_expr(val_str, local_dict=sym_dict)
                
                # แปลงเงื่อนไข (Condition) เช่น "lambda_val > 0.20" ให้กลายเป็นอสมการเชิงสัญลักษณ์
                if cond_str.lower() in ['default', 'true', 'else']:
                    cond_expr = True
                else:
                    cond_expr = parse_expr(cond_str, local_dict=sym_dict)
                
                pairs.append((val_expr, cond_expr))
            
            # ยัดโครงสร้างอสมการทั้งหมดเข้าสู่สัญลักษณ์ Piecewise ของ SymPy
            conditional_expressions[var_name] = sp.Piecewise(*pairs)

        # 4. ทำการหลอมรวม (Substitute) ตัวแปรเงื่อนไขและตัวแปรตัวกลางเข้าไปในระบบสากล
        # อัปเดต sym_dict เพื่อให้ตอนแปลงสมการหลัก มันจะดึงเอาโครงสร้างเงื่อนไขไปฝังไว้ข้างในทันที
        sym_dict.update(inter_exprs)
        sym_dict.update(conditional_expressions)

        # 5. แปลงและย้ายข้างสมการหลักตามปกติ
        parsed_eqs = [parse_expr(eq, local_dict=sym_dict) for eq in equations_strs]
        target_symbols = [sym_dict[name] for name in target_names]

        solved = sp.solve(parsed_eqs, target_symbols)
        if not solved:
            return jsonify({"error": "SymPy ไม่สามารถแก้ระบบสมการหา Target ที่ระบุได้"}), 400

        # 6. แทนค่าพารามิเตอร์คงที่
        param_subs = {sym_dict[k]: float(v) for k, v in user_params.items() if k in sym_dict and not isinstance(sym_dict[k], sp.Piecewise)}
        
        solved_exprs = {}
        for target_sym in target_symbols:
            expr = solved[target_sym] if isinstance(solved, dict) else solved[0]
            # ใช้พาวเวอร์ของ SymPy ในการกระจายการแทนค่าลึกเข้าไปในเงื่อนไขอสมการอัตโนมัติ
            solved_exprs[str(target_sym)] = expr.subs(param_subs)

        # 7. Lambdify ออกมาเป็นฟังก์ชันความเร็วสูง
        lambdify_args = [sym_dict[name] for name in state_vars_names]
        compiled_funcs = {
            name: sp.lambdify(lambdify_args, expr, 'numpy') 
            for name, expr in solved_exprs.items()
        }

        # 8. Dynamic ODE Callback Engine
        def ode_callback(t_curr, z):
            current_state_env = {name: val for name, val in zip(state_vars_names, z)}
            
            # ป้องกันข้อจำกัดฟิสิกส์ของ ABS (กรณีถ้ารถหยุดสนิท) ส่งตรงมาจากหน้าบ้านได้เช่นกัน
            if 'vx' in current_state_env and current_state_env['vx'] < 0.5:
                return [0.0] * len(state_deriv_names)

            evaluated_targets = {}
            for name, func in compiled_funcs.items():
                evaluated_targets[name] = float(func(*z))

            dz_dt = []
            for name in state_deriv_names:
                if name in current_state_env:
                    dz_dt.append(current_state_env[name])
                elif name in evaluated_targets:
                    dz_dt.append(evaluated_targets[name])
                else:
                    dz_dt.append(0.0)
                    
            return dz_dt

        # 9. รันตัวคำนวณและส่งข้อมูลกลับ
        z0 = [float(val) for val in data.get('z0', [])]
        t_end = float(data.get('t_end', 3.0))
        t_eval = np.linspace(0, t_end, int(data.get('steps', 300)))

        sol = solve_ivp(ode_callback, [0, t_end], z0, t_eval=t_eval, method='RK45')

        chart_data = []
        for i in range(len(sol.t)):
            point = {"time": float(round(sol.t[i], 3))}
            for j, name in enumerate(state_vars_names):
                val = sol.y[j][i]
                # แปลงล้อหมุนเชิงมุมให้เป็นความเร็วเชิงเส้นบนกราฟอัตโนมัติหากชื่อเป็น omega
                if name == 'omega' and 'R' in user_params:
                    point['wr'] = float(round(max(0.0, val * float(user_params['R'])), 2))
                point[name] = float(round(max(0.0, val), 4)) if name == 'vx' else float(round(val, 4))
            chart_data.append(point)

        return jsonify(chart_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    # เปิดโปรเจกต์ที่พอร์ต 3000 (หรือพอร์ตอื่นๆ ตามที่คุณสะดวก)
    app.run(debug=True, port=3000)