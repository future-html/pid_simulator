import time
import threading
from services.mqtt_service import mqtt_input_buffer, publish_output
from services.database import log_event_sync
from services.line_service import send_line_notification

class Timer:
    def __init__(self, preset_ms: int):
        self.preset = preset_ms
        self.accumulated = 0
        self.done = False

    def update(self, enable: bool, dt_ms: int):
        if enable:
            self.accumulated += dt_ms
            if self.accumulated >= self.preset:
                self.accumulated = self.preset
                self.done = True
        else:
            self.accumulated = 0
            self.done = False

simulation_state = {
    "running": False,
    "project": None,
    "variables": {},
    "timers": {},
    "previous_outputs": {},
}

simulation_thread = None

def simulate_step(project, variables, timers):
    scan_time_ms = project.get("scan_time_ms", 100)
    for rung in project["rungs"]:
        power = True
        for element in rung["elements"]:
            if element["type"] == "contact":
                var_name = element["var"]
                val = variables.get(var_name, False)
                if element["normally"] == "closed":
                    val = not val
                power = power and val
            elif element["type"] == "timer":
                timer_name = element["var"]
                if timer_name not in timers:
                    timers[timer_name] = Timer(element.get("preset", 1000))
                timer = timers[timer_name]
                timer.update(power, scan_time_ms)
                power = timer.done
    for rung in project["rungs"]:
        power = True
        set_reset = None
        coil_var = None
        for element in rung["elements"]:
            if element["type"] == "contact":
                var_name = element["var"]
                val = variables.get(var_name, False)
                if element["normally"] == "closed":
                    val = not val
                power = power and val
            elif element["type"] == "timer":
                timer_name = element["var"]
                if timer_name in timers:
                    power = power and timers[timer_name].done
                else:
                    power = False
            elif element["type"] == "coil":
                coil_var = element["var"]
                set_reset = element.get("set_reset", None)
                break
        if coil_var:
            if set_reset == "SET":
                if power:
                    variables[coil_var] = True
            elif set_reset == "RESET":
                if power:
                    variables[coil_var] = False
            else:
                variables[coil_var] = power
    return variables

def simulation_loop():
    global simulation_state
    while simulation_state["running"] and simulation_state["project"]:
        proj = simulation_state["project"]
        scan_ms = proj.get("scan_time_ms", 100) / 1000.0
        for var_name, info in proj["variables"].items():
            if info["direction"] == "input":
                if var_name in mqtt_input_buffer:
                    simulation_state["variables"][var_name] = mqtt_input_buffer[var_name]
        simulation_state["variables"] = simulate_step(
            proj, simulation_state["variables"], simulation_state["timers"]
        )
        for var_name, info in proj["variables"].items():
            if info["direction"] == "output":
                new_val = simulation_state["variables"].get(var_name, False)
                old_val = simulation_state["previous_outputs"].get(var_name, None)
                if new_val != old_val:
                    publish_output(proj["project"], var_name, new_val)
                    log_event_sync(proj["project"], var_name, str(new_val), "output")
                    send_line_notification(f"⚡ {var_name} = {new_val} (Project: {proj['project']})")
                    simulation_state["previous_outputs"][var_name] = new_val
        time.sleep(scan_ms)

def start_simulation():
    global simulation_state, simulation_thread
    if simulation_state["running"]:
        return
    simulation_state["running"] = True
    simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
    simulation_thread.start()

def stop_simulation():
    global simulation_state
    simulation_state["running"] = False
    if simulation_thread and simulation_thread.is_alive():
        simulation_thread.join(timeout=2)
