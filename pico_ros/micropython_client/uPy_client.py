# ###  Setup (Required – Do First)
# 
# 1. Update the WiFi configuration
# 
#    * Change the network name (`SSID`) in the code
# 
# 2. Create a `.env` file in your device
# 
#    * Store your WiFi password inside
# 
# 3. Configure the broker connection
# 
#    * Update the Broker IP address to match your computer
# 
# ---
# 
# ###  Core Tasks (Required)
# 
# 4. Run the system and verify:
# 
#    * Device connects to WiFi
#    * Frames are sent to the broker
#    * Messages are received in the web client
# 
# 5. Debug any issues:
# 
#    * Check serial output
#    * Verify JSON structure
#    * Validate base64 decoding in the browser
# 
# ---
# 
# ###  Extensions (Choose at least ONE)
# 
# 6. Improve the communication system
# 
#    * Add a local Pub/Sub mechanism (callbacks per topic)
# 
# 7. Improve performance
# 
#    * Replace base64 with binary transmission **(advanced)**
# 
# 8. Camera improvements
# 
#    * Replace the fake camera with the real OV7670 camera module
#    * Optionally capture frames using `_thread`
# 
# 9. Robot interaction
# 
#    * Create a new Task to control:
# 
#      * servos
#      * LEDs
#      * or other actuators
# 
# ---
# 
# ###  Reflection (Short Answer)
# 
# 10. Answer briefly:
# 
# * What is the advantage of using a Scheduler instead of a simple loop?
# * What problems does Pub/Sub solve in embedded systems?
# 
#



# To Do Now
###########
# Change the WiFi network name
# Create .env file in the RPi Pico with the password
# Update the Broker IP 

# To Do Later
#############
# OV7670 camera update; to read data on the other `_thread`.
# Creation of another task to interact with the robot.


# =============================================================
# MICRO PYTHON PUBSUB CLIENT WITH SCHEDULER
# =============================================================

import network, time, json, gc
import usocket as socket
import ubinascii
from machine import Timer

import time

class Task:
    def __init__(self, scheduler, period_ms, priority=1):
        self.period = period_ms
        self.priority = priority
        self.next_run = time.ticks_ms()
        scheduler.add(self)

    def update(self):
        pass




class Scheduler:
    def __init__(self):
        self.tasks = []

    def add(self, task):
        self.tasks.append(task)
        self.tasks.sort(key=lambda t: t.priority)

    def run(self):
        while True:
            now = time.ticks_ms()

            for task in self.tasks:
                if time.ticks_diff(now, task.next_run) >= 0:
                    task.update()
                    task.next_run = time.ticks_add(now, task.period)

            gc.collect()
            time.sleep_ms(1)



# =========================================================
# WIFI
# =========================================================
class WiFiManager:
    def __init__(self, ssid, password_file=".env"):
        self.ssid = ssid
        with open(password_file) as f:
            self.password = f.read().strip()

        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)

    def connect(self):
        print("""Connecting to WiFi...
            # Error meanings
            # 0  Link Down
            # 1  Link Join
            # 2  Link NoIp
            # 3  Link Up
            # -1 Link Fail
            # -2 Link NoNet
            # -3 Link BadAuth        
""")
        if not self.wlan.isconnected():
            self.wlan.connect(self.ssid, self.password)
            while not self.wlan.isconnected():
                time.sleep(1)
                print("wlan.status:", self.wlan.status())

        print("✅ WiFi status (3=OK):", self.wlan.status(),", IP:",self.wlan.ifconfig()[0])

#     if ap:
#         # wifi.radio.start_ap("RPi-Pico", "12345678")
#         # print("wifi.radio ap:", wifi.radio.ipv4_address_ap)
#         wlan=network.WLAN(network.AP_IF)
#         wlan.active(True)
#         wlan.config(essid="RPi-Pico", password="12345678")
#         if wlan.active():            
#             print("Current SSID",wlan.config('essid'))
#             print("IP Address:", ap.ifconfig()[0])
#         else:
#             print("AP inactive:", wlan.status())
# 
#     else:    
#         # wifi.radio.connect("Ejemplo","12345678")
#         # print("wifi.radio:", wifi.radio.ipv4_address)
#         wlan = network.WLAN(network.STA_IF)
#         wlan.active(True)
#         wlan.connect("Ejemplo","12345678")
#         for _ in range(10):
#             if wlan.isconnected():
#                 break
#             print('.',end='')
#             time.sleep(1)
#         if wlan.isconnected():
#             print("IP Address:", wlan.ifconfig())
#         else:
#             print("Falied:", wlan.status())
#             # The status() method provides connection states:
#                         # 
#             # Handle connection error
#             # Error meanings
#             # 0  Link Down
#             # 1  Link Join
#             # 2  Link NoIp
#             # 3  Link Up
#             # -1 Link Fail
#             # -2 Link NoNet
#             # -3 Link BadAuth        
# 

# =========================================================
# SOCKET CLIENT
# =========================================================
class SocketClient(Task):
    def __init__(self, host, port, scheduler, period_ms=100):
        super().__init__(scheduler, period_ms)
        self.host = host
        self.port = port
        self.sock = None
        self.actions = {}
        self._rx_buffer = b""

    def connect(self):
        print("🔌 Conectando al broker...")
        addr = socket.getaddrinfo(self.host, self.port)[0][-1]
        print('addr',addr)
        self.sock = socket.socket()
        print('sock',self.sock)
        self.sock.connect(addr)
        print('sock.connect')
        #self.sock.settimeout(0.1)
        self.sock.setblocking(False)
        print("✅ Conectado")

    def ensure(self):
        if self.sock is None:
            self.connect()

    def send(self, data):
        total = 0
        while total < len(data):
            try:
                sent = self.sock.send(data[total:])
                if sent == 0:
                    print("⚠️ Socket closed")
                    return False
                total += sent
            except OSError:
                # Socket not ready → exit and retry later
                return False
        return True


    def send_json(self, obj):
        self.send((json.dumps(obj) + "\n").encode())

    def close(self):
        try:
            if self.sock:
                self.sock.close()
        except:
            pass
        self.sock = None



    def recv_json_nonblocking(self):
        messages = []

        try:
            data = self.sock.recv(1024)

            if data == b'':
                print("⚠️ Connection closed by peer")
                self.close()
                return []

            if data:
                self._rx_buffer += data

        except OSError:
            # No data available (non-blocking)
            return []

        while b"\n" in self._rx_buffer:
            line, self._rx_buffer = self._rx_buffer.split(b"\n", 1)

            if not line:
                continue

            try:
                messages.append(json.loads(line))
            except Exception as e:
                print("JSON error:", e)
                print("Bad line:", line)

        return messages



    def update(self):
        msgs = self.recv_json_nonblocking()
        for msg in msgs:
            action = msg.get("action")
            if action in self.actions:
                self.actions[action](msg)
        
    def add_action(self, action, callback):
        self.actions[action] = callback        



# =========================================================
# PUBSUB CLIENT
# =========================================================
class Node:
    def __init__(self, socket_client, prefix='UDFJC/emb1/robot0/'):
        self.sock = socket_client
        self.sock.add_action("PUB", self.handle_pub)
        self.sock.add_action("SUB", self.handle_sub)
        self.prefix=prefix
        self.subscriptions = {}  # topic -> set(callback)

    def publish(self, topic, data):
        self.broker_publish(topic,data)
        self.local_publish(topic,data)
       
    def broker_publish(self,topic,data):   
        self.sock.ensure()

        pkt = {
            "action": "PUB",
            "topic": self.prefix+topic,
            "data": data
        }

        self.sock.send_json(pkt)


    def local_publish(self,topic,data):   
        callbacks = self.subscriptions.get(topic, set())

        print(f"[PUB] {topic} -> {len(callbacks)} callbacks")

        for c in list(callbacks):
            #if c != origin:
                try:
                    c(data)
                except:
                    callbacks.remove(c)
                    print("Remove from topic",topic,"callback",c)


    def subscribe(self, topic,callback ):#topic without prefix
        self.subscriptions.setdefault(topic, set()).add(callback)
        self.sock.ensure()

        pkt = {
            "action": "SUB",
            "topic": self.prefix+topic,
        }
        self.sock.send_json(pkt)
        print(f"[SUB] {callback} -> {topic}")

    def handle_pub(self, msg):
        topic = msg['topic']

        if not topic.startswith(self.prefix):
            return  # ignore чужое

        local_topic = topic[len(self.prefix):]

        print('Node.handle_pub', local_topic)

        self.local_publish(local_topic, msg['data'])

    def handle_sub(self,msg):
        print('Node.handle_sub ignored',msg)




# =========================================================
# SCHEDULER SYSTEM
# =========================================================
# ⚠ Important limitation
# 
# If a task blocks:
# 
# time.sleep(2)
# 
#  EVERYTHING stops
# 
# So:
# 
# ✔ Keep tasks fast
# ✔ No blocking calls
# ✔ Use state machines if needed



#################### TASKS #################


class WatchdogTask(Task):
    def __init__(self, scheduler, pubsub, period_ms=60000):
        super().__init__(scheduler, period_ms)
        self.pubsub = pubsub

    def update(self):
            self.pubsub.publish(
                "debug/watchdog",
                {"msg": "alive"}
            )
            print("🐶 Watchdog")
            

class CameraPublisherTask(Task):
    # Upgrade to the real ov7670 camera, it could read the data on the other `_thread`
    def __init__(self, scheduler, pubsub, width=40, height=30, period_ms=20000):
        super().__init__(scheduler, period_ms)

        self.pubsub = pubsub
        self.WIDTH = width
        self.HEIGHT = height
        self.buf = bytearray(width * height * 2)

#        self.last = 0
#        self.interval = 2

    def update(self):
        #now = time.time()

        #if now - self.last > self.interval:
#            gc.collect()

            frame = self._generate_frame()
#            frame_b64 = ubinascii.b2a_base64(frame).decode().strip()
            frame_b64 = ubinascii.b2a_base64(frame).decode().replace("\n", "")

            self.pubsub.publish(
                "camera/frame",
                {
                    "w": self.WIDTH,
                    "h": self.HEIGHT,
                    "frame": frame_b64
                }
            )

            print("📤 Frame")
            #self.last = now

    def _generate_frame(self):
        t = int(time.time()) % 60

        r = (t * 10) % 256
        g = (128 + t * 15) % 256
        b = (255 - t * 35) % 256

        color = self.rgb565(r, g, b)

        hi = (color >> 8) & 0xFF
        lo = color & 0xFF

        for i in range(0, len(self.buf), 2):
            self.buf[i] = hi
            self.buf[i + 1] = lo

        return self.buf

    def rgb565(self, r, g, b):
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

#===========================================

class Arm(Task):
    def __init__(self, scheduler, pubsub,joint_state, period_ms=30000):
        super().__init__(scheduler, period_ms)
        self.pubsub = pubsub
        self.joint_state = joint_state
        pubsub.subscribe("arm/joint_state",self.handle_message )

    def update(self):
#             self.pubsub.publish(
#                 "arm/update",
#                 {"JointState": str(joint_state)}
#             )
            print("Arm.update()",self.joint_state)

    def handle_message(self, msg):
           print("Arm.handle_message()",msg)
           self.joint_state.update(msg)

class Car(Task):
    def __init__(self, scheduler, pubsub, twist , period_ms=30000):
        super().__init__(scheduler, period_ms)
        self.pubsub = pubsub
        self.twist = twist
        pubsub.subscribe("car/car_vel",self.handle_message )

    def update(self):
#             self.pubsub.publish(
#                 "car/update",
#                 {"Twist": str(twist)}
#             )
            print("Car.update()",self.twist)

    def handle_message(self, msg):
           print("Car.handle_message()",msg)
           self.twist.update(msg)
           

#===============
# class Vector3:
#     def __init__(self, x=0.0, y=0.0, z=0.0):
#         self.x = x
#         self.y = y
#         self.z = z
# 
# class Twist:
#     def __init__(self):
#         self.linear = Vector3() # lineal vel m/s
#         self.angular = Vector3() # angular vel rad/s
#
# 
# class JointState:
#     def __init__(self, name,position):
#         self.name = name
#         self.position = position 
# =========================================================
# MAIN APP
# =========================================================
class MainApp:
    def __init__(self):

        self.scheduler = Scheduler()
        self.wifi = WiFiManager("Ejemplo") # Ejemplo  Change to your WiFi
        self.socket = SocketClient(host="192.168.1.17", port=5051,scheduler=self.scheduler) #192.168.1.100  # Change to the Broker IP
        self.pubsub = Node(self.socket, prefix='UDFJC/emb1/robot0/')
        self.watchdog = WatchdogTask(scheduler=self.scheduler, pubsub=self.pubsub)
        self.camera = CameraPublisherTask(scheduler=self.scheduler, pubsub=self.pubsub, width=40, height=30)
        self.arm = Arm(scheduler=self.scheduler, pubsub=self.pubsub,joint_state={"shoulder": 10, "elbow": 20, "wrist": 30})
        self.car = Car(scheduler=self.scheduler, pubsub=self.pubsub,twist = {"linear": 0.0,"angular": 0.0})
 

    def run(self):
        self.wifi.connect()
        print("🚀 Scheduler running...")
        self.scheduler.run()


# =========================================================
# ENTRY POINT
# =========================================================
app = MainApp()
app.run()