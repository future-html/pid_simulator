import os
import certifi
import numpy as np
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
from sympy import sqrt, exp, sin, cos, log # เพิ่มฟังก์ชันคณิตศาสตร์ที่จำเป็น

load_dotenv()

app = Flask(__name__)
CORS(app)

# --- MQTT Configuration ---
NETPIE_CLIENT_ID = "427e0ae3-fd74-471a-8cc6-3f4dfc7d3641"   
NETPIE_TOKEN = "W8xAzJNmSQAD3DnMZk9kU4DQAC3hksvs"           
NETPIE_SECRET = "xq79QfBmDBYQ4ni3fnoXVwjfvfy3k2mg"
NETPIE_BROKER = os.getenv("NETPIE_BROKER", "broker.netpie.io")

mqtt_client = mqtt.Client(client_id=NETPIE_CLIENT_ID, protocol=mqtt.MQTTv311)
mqtt_client.username_pw_set(NETPIE_TOKEN, NETPIE_SECRET)
mqtt_lock = Lock()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to NETPIE MQTT broker")
    else:
        print(f"❌ Connection failed with code {rc}")
mqtt_client.on_connect = on_connect

try:
    mqtt_client.connect(NETPIE_BROKER, 1883, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"❌ MQTT connection error: {e}")

# --- MongoDB Connection ---
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
try:
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB!")
except ConnectionFailure:
    print("❌ Failed to connect to MongoDB.")
db = client['sample_mflix']
users_collection = db['users']

# --- PID Controller Class (修复 2: 补充缺失的 PID 类) ---
class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.prev_error = 0
        self.integral = 0

    def compute(self, current_value, dt):
        error = self.setpoint - current_value
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt if dt > 0 else 0
        self.prev_error = error
        return self.Kp * error + self.Ki * self.integral + self.Kd * derivative

# --- API Routes ---

@app.route('/api/shadow/update', methods=['POST'])
def update_shadow():
    sensor_data = request.get_json()
    if not sensor_data:
        return jsonify({"error": "No data provided"}), 400

    shadow_payload = {"data": sensor_data}
    payload_string = json.dumps(shadow_payload)
    topic = "@shadow/data/update"

    max_retries = 5
    retry_delay = 1.0
    attempt = 0

    while attempt < max_retries:
        attempt += 1
        if not mqtt_client.is_connected():
            print(f"⚠️ [Attempt {attempt}/{max_retries}] MQTT client offline. Waiting...")
            time.sleep(retry_delay)
            continue

        try:
            with mqtt_lock:
                result = mqtt_client.publish(topic, payload_string, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                return jsonify({
                    "status": "Shadow updated successfully",
                    "attempts": attempt,
                    "topic": topic,
                    "payload_sent": shadow_payload
                }), 200
            print(f"⚠️ [Attempt {attempt}/{max_retries}] Publish failed with code {result.rc}")
        except Exception as e:
            print(f"❌ [Attempt {attempt}/{max_retries}] Error: {e}")
        time.sleep(retry_delay)

    return jsonify({"error": f"Failed to update shadow after {max_retries} attempts."}), 503


@app.route('/users', methods=['GET'])
def get_users():
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
    data = request.get_json()
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({"error": "Missing name or email"}), 400
    new_user = {"name": data['name'], "email": data['email']}
    try:
        result = users_collection.insert_one(new_user)
        return jsonify({"message": "User created successfully", "id": str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 修复 1: 新增专门的公式解析器，解决 "invalid syntax (<string>, line 1)" 问题
def parse_equation(equation_str, sym_dict):
    """
    处理包含 "=" 的方程式，将其转换为 SymPy 的 Eq() 对象。
    """
    if '=' in equation_str:
        lhs, rhs = equation_str.split('=', 1)
        lhs_expr = parse_expr(lhs.strip(), local_dict=sym_dict)
        rhs_expr = parse_expr(rhs.strip(), local_dict=sym_dict)
        return sp.Eq(lhs_expr, rhs_expr)
    return parse_expr(equation_str, local_dict=sym_dict)


@app.route('/api/simulate/universal', methods=['POST'])
def universal_simulate():
    try:
        data = request.get_json() or {}
        
        state_vars_names = data.get('state_vars', [])       
        state_deriv_names = data.get('state_derivatives', []) 
        target_names = data.get('targets', [])               
        user_params = data.get('params', {})                
        equations_strs = data.get('equations', [])   

        # 1. Base Symbols
        sym_dict = {'t': sp.Symbol('t'), 'sqrt': sp.sqrt, 'exp': sp.exp, 'sin': sp.sin, 'cos': sp.cos, 'log': sp.log}
        all_names = state_vars_names + state_deriv_names + target_names + list(user_params.keys()) + list(data.get('intermediates',{}).keys()) + list(data.get('conditions',{}).keys())
        for name in all_names:
            if name not in sym_dict: sym_dict[name] = sp.Symbol(name)

        # 2. Replace constant params in symbols
        param_subs = {sym_dict[k]: float(v) for k, v in user_params.items()}

        # 3. Parse INTERMEDIATES (Substitute params immediately)
        intermediates_data = data.get('intermediates', {})
        inter_exprs = {k: parse_expr(v, local_dict=sym_dict).subs(param_subs) for k, v in intermediates_data.items()}

        # 4. Parse CONDITIONS (เตรียม Logic สำหรับ Python Runtime)
        conditions_data = data.get('conditions', {})
        
        # 5. Parse EQUATIONS
        def parse_equation(eq_str):
            if '=' in eq_str:
                lhs, rhs = eq_str.split('=', 1)
                return sp.Eq(parse_expr(lhs.strip(), local_dict=sym_dict), parse_expr(rhs.strip(), local_dict=sym_dict))
            return parse_expr(eq_str, local_dict=sym_dict)

        parsed_eqs = [parse_equation(eq) for eq in equations_strs]
        target_symbols = [sym_dict[name] for name in target_names]

        solved = sp.solve(parsed_eqs, target_symbols)
        if not solved:
            return jsonify({"error": "SymPy ไม่สามารถแก้ระบบสมการหา Target ที่ระบุได้"}), 400

        # 6. แก้สมการหา Target และแทนค่า Params (คง Symbol `conditions` และ `intermediates` ไว้)
        solved_exprs = {}
        for target_sym in target_symbols:
            expr = solved[target_sym] if isinstance(solved, dict) else solved[0]
            solved_exprs[str(target_sym)] = expr.subs(param_subs)

        # 7. สร้าง Compiled Functions สำหรับ ODE Callback
        all_lambdify_args = [sym_dict[n] for n in state_vars_names] + [sym_dict[n] for n in intermediates_data.keys()] + [sym_dict[n] for n in conditions_data.keys()]
        
        compiled_derivatives = {}
        for name, expr in solved_exprs.items():
            compiled_derivatives[name] = sp.lambdify(all_lambdify_args, expr, 'numpy')

        # 8. สร้าง Compiled Functions สำหรับตัวแปรตัวกลาง (Intermediates)
        inter_funcs = {}
        inter_args = [sym_dict[n] for n in state_vars_names]
        for k, expr in inter_exprs.items():
            inter_funcs[k] = sp.lambdify(inter_args, expr, 'numpy')

        # 9. สร้าง Python Logic สำหรับ Conditions (แทนที่ Piecewise)
        condition_logic = {}
        for cond_var_name, cond_map in conditions_data.items():
            logic_list = []
            default_val = None
            
            for cond_str, val_str in cond_map.items():
                if cond_str.lower() in ['default', 'true', 'else']:
                    # ถ้าเป็น Default ให้แปลงเป็นค่าคงที่ทันที
                    default_val = float(parse_expr(val_str, local_dict=sym_dict).subs(param_subs))
                else:
                    # สร้าง Checker (คืน True/False)
                    cond_lambda = sp.lambdify(inter_args, parse_expr(cond_str, local_dict=sym_dict), 'numpy')
                    # สร้าง Value Assigner
                    val_lambda = sp.lambdify(inter_args, parse_expr(val_str, local_dict=sym_dict).subs(param_subs), 'numpy')
                    logic_list.append((cond_lambda, val_lambda))
            
            # เก็บรายการเช็คและค่า Default
            condition_logic[cond_var_name] = (logic_list, default_val)

        # 10. ODE Callback (ทำงานใน Python จริง ไม่ใช้ SymPy Piecewise)
        def ode_callback(t_curr, z):
            # คำนวณ Intermediates (เช่น lambda_val)
            inter_values = {}
            for name, func in inter_funcs.items():
                inter_values[name] = float(func(*z))
            
            # คำนวณ Conditions (ใช้ Logic Python ตรวจสอบ)
            cond_values = {}
            for var_name, (checks, default) in condition_logic.items():
                found = False
                # `args` ที่จะป้อนให้กับ Condition และ Value lambda
                args_for_checks = list(z) + [inter_values[n] for n in intermediates_data.keys()]
                
                for cond_lambda, val_lambda in checks:
                    try:
                        if bool(cond_lambda(*args_for_checks)):
                            cond_values[var_name] = float(val_lambda(*args_for_checks))
                            found = True
                            break
                    except Exception:
                        pass
                
                if not found and default is not None:
                    cond_values[var_name] = default
            
            # คำนวณ Derivatives (Targets) โดยส่งตัวแปรทั้งหมดลงไป
            eval_args = list(z) + [inter_values[n] for n in intermediates_data.keys()] + [cond_values[n] for n in conditions_data.keys()]
            
            evaluated_targets = {}
            for name, func in compiled_derivatives.items():
                try:
                    evaluated_targets[name] = float(func(*eval_args))
                except (ZeroDivisionError, ValueError):
                    evaluated_targets[name] = 0.0

            dz_dt = []
            for name in state_deriv_names:
                if name in state_vars_names: # ถ้าเป็น State ตายตัว (เช่น v = dx/dt)
                    dz_dt.append(z[state_vars_names.index(name)])
                elif name in evaluated_targets: # ถ้าเป็นความเร่งหรือแรง (เช่น a = dV/dt)
                    dz_dt.append(evaluated_targets[name])
                else:
                    dz_dt.append(0.0)
            return dz_dt

        # 11. Run Simulation
        z0 = [float(val) for val in data.get('z0', [])]
        t_end = float(data.get('t_end', 3.0))
        steps = int(data.get('steps', 300))
        t_eval = np.linspace(0, t_end, steps)

        sol = solve_ivp(ode_callback, [0, t_end], z0, t_eval=t_eval, method='RK45')

        # 12. Format Data to send back
        chart_data = []
        for i in range(len(sol.t)):
            point = {"time": float(round(sol.t[i], 3))}
            for j, name in enumerate(state_vars_names):
                val = sol.y[j][i]
                if name == 'omega' and 'R' in user_params:
                    point['wr'] = float(round(max(0.0, val * float(user_params['R'])), 2))
                point[name] = float(round(max(0.0, val), 4)) if name == 'vx' else float(round(val, 4))
            chart_data.append(point)

        return jsonify(chart_data), 200

    except Exception as e:
        # เพิ่ม traceback เพื่อดู Error จริงๆ ตอน Debug
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/simulate/pid', methods=['POST'])
def pid_simulate():
    data = request.get_json() or {}
    Kp = data.get('Kp', 1.0)
    Ki = data.get('Ki', 0.1)
    Kd = data.get('Kd', 0.05)
    setpoint = data.get('setpoint', 50.0)
    t_end = data.get('t_end', 10.0)
    dt = data.get('dt', 0.1)
    z0 = data.get('z0', 0.0)
    
    pid = PIDController(Kp, Ki, Kd, setpoint) # 调用已补充的 PID 类
    results = []
    state = z0
    steps = int(t_end / dt)
    
    for i in range(steps):
        t = i * dt
        u = pid.compute(state, dt)
        dzdt = -0.1 * state + u
        state += dzdt * dt
        results.append({"time": round(t, 2), "value": round(float(state), 4)})
        
    return jsonify(results), 200


if __name__ == '__main__':
    app.run(debug=True, port=3000)