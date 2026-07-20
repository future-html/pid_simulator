import json
import time
import paho.mqtt.client as mqtt
import requests
from config import config

MQTT_SUB_TOPIC = "@shadow/data/update"

def get_mqtt_client():
    if not config.USE_MQTT:
        return None
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=config.NETPIE_CLIENT_ID, protocol=mqtt.MQTTv311)
    client.username_pw_set(config.NETPIE_TOKEN, config.NETPIE_SECRET)
    return client

def publish_shadow(data: dict) -> bool:
    if config.USE_MQTT:
        return _publish_shadow_mqtt(data)
    else:
        return _publish_shadow_rest(data)

def _publish_shadow_mqtt(data: dict) -> bool:
    client = get_mqtt_client()
    if client is None:
        return False

    conn_ok = False
    def on_connect(client, userdata, flags, reasonCode, properties=None):
        nonlocal conn_ok
        conn_ok = (reasonCode == 0)

    client.on_connect = on_connect
    client.connect(config.NETPIE_BROKER, 1883, 60)
    client.loop_start()

    timeout = 3
    start = time.time()
    while not conn_ok and (time.time() - start) < timeout:
        time.sleep(0.1)

    if not conn_ok:
        client.loop_stop()
        client.disconnect()
        return False

    topic = "@shadow/data/update"
    payload = json.dumps({"data": data})
    try:
        result = client.publish(topic, payload, qos=1)
        ok = result.rc == mqtt.MQTT_ERR_SUCCESS
        client.loop_stop()
        client.disconnect()
        return ok
    except Exception:
        client.loop_stop()
        client.disconnect()
        return False

def _publish_shadow_rest(data: dict) -> bool:
    url = "https://api.netpie.io/v2/device/shadow/data"
    headers = {
        "Authorization": f"Device {config.NETPIE_CLIENT_ID}:{config.NETPIE_TOKEN}",
        "Content-Type": "application/json"
    }
    try:
        resp = requests.put(url, json={"data": data}, headers=headers, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False

# สำหรับ MQTT Subscriber (สำหรับ Auto Alert)
def start_mqtt_subscriber(callback_func):
    if config.IS_VERCEL:
        print("ℹ️ Vercel skipped MQTT Subscriber.")
        return None
    
    client = get_mqtt_client()
    if client is None:
        return None

    def on_connect(client, userdata, flags, reasonCode, properties=None):
        if reasonCode == 0:
            print("✅ MQTT Subscriber connected")
            client.subscribe(MQTT_SUB_TOPIC, qos=1)
        else:
            print(f"❌ MQTT Subscriber connect failed: {reasonCode}")

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            callback_func(payload)
        except Exception as e:
            print(f"MQTT parse error: {e}")

    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(config.NETPIE_BROKER, 1883, 60)
        client.loop_start()
        return client
    except Exception as e:
        print(f"MQTT Start Failed: {e}")
        return None
