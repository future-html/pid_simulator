import json
import time
import paho.mqtt.client as mqtt
from threading import Lock
from config.settings import (
    NETPIE_CLIENT_ID, NETPIE_TOKEN, NETPIE_SECRET, NETPIE_BROKER
)

mqtt_client = mqtt.Client(client_id=NETPIE_CLIENT_ID, protocol=mqtt.MQTTv311)
mqtt_client.username_pw_set(NETPIE_TOKEN, NETPIE_SECRET)
mqtt_lock = Lock()
mqtt_input_buffer = {}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to NETPIE MQTT broker")
    else:
        print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    parts = topic.replace("@msg/", "").split("/")
    if len(parts) >= 3 and parts[-2] == "Input":
        var_name = parts[-1]
        try:
            value = json.loads(payload).get("value", payload)
        except:
            value = payload
        mqtt_input_buffer[var_name] = value
        print(f"MQTT Input: {var_name} = {value}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def connect_mqtt():
    try:
        mqtt_client.connect(NETPIE_BROKER, 1883, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"❌ MQTT connection error: {e}")

def subscribe_inputs(project: str, variables: dict):
    for var_name, info in variables.items():
        if info["direction"] == "input":
            topic = f"@msg/{project}/Input/{var_name}"
            mqtt_client.subscribe(topic)
            print(f"Subscribed {topic}")

def publish_output(project: str, var_name: str, value):
    topic = f"@msg/{project}/Output/{var_name}"
    payload = json.dumps({"value": value})
    mqtt_client.publish(topic, payload)
    print(f"Published {topic}: {value}")

def publish_shadow(data_dict, topic="@shadow/data/update"):
    payload = json.dumps({"data": data_dict})
    max_retries = 5
    for attempt in range(1, max_retries+1):
        if not mqtt_client.is_connected():
            time.sleep(1)
            continue
        with mqtt_lock:
            result = mqtt_client.publish(topic, payload, qos=1)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            return True, attempt
        time.sleep(1)
    return False, attempt
