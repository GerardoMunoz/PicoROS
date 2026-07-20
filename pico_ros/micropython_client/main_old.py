import network
import socket
import time
import json
from machine import Pin, ADC

# =========================
# CONFIGURACIÓN
# =========================
SSID = "And"
PASSWORD = "Andresc27"
PORT = 5000
SLAVE_ID = 1

CYCLE_TIMEOUT_MS = 1500

# =========================
# HARDWARE
# =========================
led = Pin("LED", Pin.OUT)
sw1 = Pin(14, Pin.IN, Pin.PULL_UP)
temp_sensor = ADC(4)

# =========================
# MEMORIA DE PROCESO
# =========================
inputs = {
    "I0_SWITCH": 0,
    "I1_WATCHDOG_OK": 1,
    "I2_TEMP_C": 0.0
}

outputs = {
    "Q0_LED": 0,
    "Q1_BLINK_ENABLE": 0
}

status = {
    "state": "INIT",
    "frames_ok": 0,
    "frames_error": 0,
    "last_seq": -1,
    "wkc": 0,
    "cycle_us": 0
}

last_frame_time = time.ticks_ms()
blink_state = 0
last_blink = time.ticks_ms()

# =========================
# FUNCIONES
# =========================
def checksum(obj):
    total = 0

    def walk(x):
        nonlocal total

        if isinstance(x, dict):
            for k in sorted(x.keys()):
                if k != "checksum":
                    walk(k)
                    walk(x[k])
        elif isinstance(x, list):
            for item in x:
                walk(item)
        else:
            for c in str(x):
                total += ord(c)

    walk(obj)
    return total % 256


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    print("Conectando WiFi...")
    while not wlan.isconnected():
        time.sleep(0.3)
        print(".", end="")

    print("\nConectado")
    print("IP:", wlan.ifconfig()[0])


def read_inputs():
    inputs["I0_SWITCH"] = 1 if sw1.value() == 0 else 0

    # Sensor de temperatura interno del RP2040/RP2350
    raw = temp_sensor.read_u16()
    voltage = raw * 3.3 / 65535
    inputs["I2_TEMP_C"] = round(27 - (voltage - 0.706) / 0.001721, 1)


def apply_outputs():
    global blink_state, last_blink

    if outputs["Q1_BLINK_ENABLE"] == 1:
        now = time.ticks_ms()
        if time.ticks_diff(now, last_blink) >= 250:
            blink_state = 1 - blink_state
            led.value(blink_state)
            last_blink = now
    else:
        led.value(outputs["Q0_LED"])


def update_watchdog():
    now = time.ticks_ms()
    ok = time.ticks_diff(now, last_frame_time) < CYCLE_TIMEOUT_MS

    inputs["I1_WATCHDOG_OK"] = 1 if ok else 0

    if not ok and status["state"] == "OP":
        status["state"] = "SAFEOP"
        outputs["Q0_LED"] = 0
        outputs["Q1_BLINK_ENABLE"] = 0
        led.value(0)


def change_state(command):
    if command == "CONFIG":
        status["state"] = "PREOP"
    elif command == "SAFE":
        status["state"] = "SAFEOP"
    elif command == "START":
        status["state"] = "OP"
    elif command == "STOP":
        status["state"] = "SAFEOP"
        outputs["Q0_LED"] = 0
        outputs["Q1_BLINK_ENABLE"] = 0


def process_frame(frame):
    global last_frame_time

    t0 = time.ticks_us()

    received_checksum = frame.get("checksum", -1)

    if received_checksum != checksum(frame):
        status["frames_error"] += 1
        status["wkc"] = 0
        return build_response(frame, "Checksum incorrecto")

    seq = frame.get("seq", -1)
    command = frame.get("command", "")
    out_data = frame.get("outputs", {})

    status["last_seq"] = seq
    last_frame_time = time.ticks_ms()

    change_state(command)

    if status["state"] == "OP":
        if "Q0_LED" in out_data:
            outputs["Q0_LED"] = int(out_data["Q0_LED"])

        if "Q1_BLINK_ENABLE" in out_data:
            outputs["Q1_BLINK_ENABLE"] = int(out_data["Q1_BLINK_ENABLE"])

    read_inputs()
    apply_outputs()

    status["frames_ok"] += 1
    status["wkc"] = 1
    status["cycle_us"] = time.ticks_diff(time.ticks_us(), t0)

    return build_response(frame, "")


def build_response(frame, error):
    response = {
        "seq": frame.get("seq", -1),
        "slave_id": SLAVE_ID,
        "inputs": inputs,
        "outputs": outputs,
        "status": status,
        "error": error
    }

    response["checksum"] = checksum(response)
    return response


# =========================
# PROGRAMA PRINCIPAL
# =========================
connect_wifi()

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("0.0.0.0", PORT))
server.listen(1)

status["state"] = "INIT"

print("Slave EtherCAT simulado listo")
print("Esperando Master...")

while True:
    client, addr = server.accept()
    print("Master conectado:", addr)

    buffer = ""

    while True:
        try:
            update_watchdog()
            apply_outputs()

            data = client.recv(512)

            if not data:
                break

            buffer += data.decode()

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)

                if line.strip() == "":
                    continue

                try:
                    frame = json.loads(line)
                    response = process_frame(frame)
                except Exception as e:
                    status["frames_error"] += 1
                    response = build_response({"seq": -1}, "Frame invalido")

                client.send((json.dumps(response) + "\n").encode())

        except Exception as e:
            print("Error:", e)
            break

    client.close()
    status["state"] = "SAFEOP"
    led.value(0)
    print("Master desconectado")