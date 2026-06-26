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

load_dotenv()

app = Flask(__name__)
CORS(app)

# --- MQTT Configuration ---
NETPIE_CLIENT_ID = "6826f59b-2946-42d2-9e53-a9a1533b48ae"   
NETPIE_TOKEN = "GtwtxGhzzthujCjMCmvnBEjKHp5yiJED"           
NETPIE_SECRET = "Lk3KRid62qhFgJ4smTJKnPtGVTKgA8RZ"
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


@app.route('/api/simulate/universal', methods=['POST'])
def universal_simulate():
    try:
        data = request.get_json() or {}
        return_pipeline = data.get('return_pipeline', False)

        state_vars_names = data.get('state_vars', [])       
        state_deriv_names = data.get('state_derivatives', []) 
        target_names = data.get('targets', [])              
        user_params = data.get('params', {})                
        equations_strs = data.get('equations', [])   
        intermediates_data = data.get('intermediates', {})
        conditions_data = data.get('conditions', {})

        # --- Step 0: Create Symbols and Math Functions ---
        sym_dict = {
            't': sp.Symbol('t'), 
            'sqrt': sp.sqrt, 'exp': sp.exp, 
            'sin': sp.sin, 'cos': sp.cos, 'log': sp.log
        }
        all_names = state_vars_names + state_deriv_names + target_names + list(user_params.keys()) + list(intermediates_data.keys()) + list(conditions_data.keys())
        for name in all_names:
            if name not in sym_dict: 
                sym_dict[name] = sp.Symbol(name)

        # --- Step 1: Replace Parameters with Floats ---
        param_subs = {sym_dict[k]: float(v) for k, v in user_params.items()}

        # --- Step 2: Pre-Compile Intermediates (Lambdify) ---
        inter_args = [sym_dict[n] for n in state_vars_names] + [sp.Symbol('t')]
        inter_funcs = {}
        for k, v in intermediates_data.items():
            expr = parse_expr(v, local_dict=sym_dict).subs(param_subs)
            inter_funcs[k] = sp.lambdify(inter_args, expr, 'numpy')

       # --- Step 3: Pre-Compile Conditions (Lambdify) ---
        cond_args = [sym_dict[n] for n in state_vars_names] + [sp.Symbol('t')] + [sym_dict[n] for n in intermediates_data.keys()]
        cond_funcs = {}
        
        for var_name, cond_map in conditions_data.items():
            logic_blocks = []
            default_lambda = None
            for cond_str, val_str in cond_map.items():
                # Parse and lambdify the return value for ALL branches
                val_expr = parse_expr(val_str, local_dict=sym_dict).subs(param_subs)
                val_lambdified = sp.lambdify(cond_args, val_expr, 'numpy')
                
                if cond_str.lower() in ['default', 'true', 'else']:
                    default_lambda = val_lambdified
                else:
                    cond_lambda = sp.lambdify(cond_args, parse_expr(cond_str, local_dict=sym_dict), 'numpy')
                    logic_blocks.append((cond_lambda, val_lambdified))
            
            cond_funcs[var_name] = (logic_blocks, default_lambda)

        # --- Step 4: Solve Algebraic System Simultaneously ---
        def parse_equation(eq_str):
            if '=' in eq_str:
                lhs, rhs = eq_str.split('=', 1)
                return sp.Eq(parse_expr(lhs.strip(), local_dict=sym_dict), parse_expr(rhs.strip(), local_dict=sym_dict))
            return sp.Eq(parse_expr(eq_str, local_dict=sym_dict), 0)

        parsed_eqs = [parse_equation(eq) for eq in equations_strs]
        target_symbols = [sym_dict[name] for name in target_names]
        
        # Explicitly use dict=True to guarantee a dictionary output list structure
        solved = sp.solve(parsed_eqs, target_symbols, dict=True)
        if not solved:
            return jsonify({"error": "SymPy could not solve the algebraic target equations."}), 400
        
        solved_dict = solved[0]

        # --- Step 5: Parameter Substitution & Lambdify Derivatives ---
        solved_exprs = {}
        equations_response = []
        for target_sym in target_symbols:
            expr = solved_dict.get(target_sym)
            if expr is None:
                continue
            substituted_expr = expr.subs(param_subs)
            equations_response.append(f"{target_sym} = {substituted_expr}")
            
            # Only track the targets required for state derivatives evaluation
            if str(target_sym) in state_deriv_names:
                solved_exprs[str(target_sym)] = substituted_expr

        deriv_args = [sym_dict[n] for n in state_vars_names] + [sp.Symbol('t')] + [sym_dict[n] for n in intermediates_data.keys()] + [sym_dict[n] for n in conditions_data.keys()]
        deriv_funcs = {name: sp.lambdify(deriv_args, expr, 'numpy') for name, expr in solved_exprs.items()}

        # --- Step 6: Build Pipeline Inspection Data ---
        pipeline_steps = {}
        if return_pipeline:
            pipeline_steps = {
                "1. Raw Input": equations_strs,
                "2. Parsed": [str(eq) for eq in parsed_eqs],
                "3. Solved System": {str(k): str(v) for k, v in solved_dict.items()},
                "4. Substituted": {k: str(v) for k, v in solved_exprs.items()},
                "5. Pre-Compiled Lambda Args": [str(a) for a in deriv_args],
            }

        # --- Step 7: Optimized High-Speed ODE Callback Loop ---
        def ode_callback(t_curr, z):
            # A. Evaluate Intermediates Safely
            inter_vals = {}
            args_1 = list(z) + [t_curr]
            for k, func in inter_funcs.items():
                try:
                    res = func(*args_1)
                    inter_vals[k] = float(res.item() if isinstance(res, np.ndarray) else res)
                except Exception:
                    inter_vals[k] = 0.0

           # B. Evaluate Conditional States Safely (ABS Loop Logic)
            cond_vals = {}
            args_2 = list(z) + [t_curr] + [inter_vals[n] for n in intermediates_data.keys()]
            
            for var_name, (checks, default_lambda) in cond_funcs.items():
                found = False
                for cond_lambda, val_lambda in checks:
                    try:
                        if bool(cond_lambda(*args_2)):
                            res = val_lambda(*args_2)
                            cond_vals[var_name] = float(res.item() if isinstance(res, np.ndarray) else res)
                            found = True
                            break
                    except Exception:
                        pass
                
                # Evaluate the default lambda if no previous conditions were met
                if not found and default_lambda is not None:
                    try:
                        res = default_lambda(*args_2)
                        cond_vals[var_name] = float(res.item() if isinstance(res, np.ndarray) else res)
                    except Exception:
                        cond_vals[var_name] = 0.0

            # C. Evaluate System Accelerations / Derivatives
            eval_args = list(z) + [t_curr] + [inter_vals[n] for n in intermediates_data.keys()] + [cond_vals[n] for n in conditions_data.keys()]
            evaluated_targets = {}
            for name, func in deriv_funcs.items():
                try:
                    res = func(*eval_args)
                    evaluated_targets[name] = float(res.item() if isinstance(res, np.ndarray) else res)
                except Exception:
                    evaluated_targets[name] = 0.0

            # D. Map Outputs to the Proper State Ordering
            dz_dt = []
            for name in state_deriv_names:
                if name in state_vars_names:
                    dz_dt.append(z[state_vars_names.index(name)])
                elif name in evaluated_targets:
                    dz_dt.append(evaluated_targets[name])
                else:
                    dz_dt.append(0.0)
            return dz_dt

        # --- Step 8: Execute Numerical IVP Solver ---
        z0 = [float(val) for val in data.get('z0', [])]
        t_end = float(data.get('t_end', 3.0))
        steps = int(data.get('steps', 300))
        t_eval = np.linspace(0, t_end, steps)

        sol = solve_ivp(ode_callback, [0, t_end], z0, t_eval=t_eval, method='RK45')

        # --- Step 9: Structure Response Array ---
        chart_data = []
        for i in range(len(sol.t)):
            point = {"time": float(round(sol.t[i], 3))}
            for j, name in enumerate(state_vars_names):
                val = sol.y[j][i] if i < len(sol.y[j]) else 0.0
                point[name] = float(round(val, 4))
            chart_data.append(point)

        response_body = {
            "success": bool(sol.success),
            "data": chart_data,
            "equations": equations_response,
            "initial_state": {name: float(z0[i]) for i, name in enumerate(state_vars_names)}
        }
        if return_pipeline:
            response_body["pre_solve_pipeline"] = pipeline_steps

        return jsonify(response_body), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=3000)
