from dummy_local_pubsub_chain import DummyLocalPubSubChain
from watchdog_task import WatchdogTask
from follow_line_control import FollowLineControl
from camera_simulator import CameraSimulator
from car_simulator import CarSimulator
from scheduler import Scheduler
from wifi_manager import WiFiManager
from socket_client import SocketClient
from node import Node
from pubsub_tcp import PubSubTCP
from pubsub_mqtt import PubSubMQTT



ssid="Ejemplo"
password_file=".env"
TCP_host="192.168.0.101"
TCP_port=5051
MQTT_broker="192.168.0.101"
node_name='emb_node_0'
prefix='UDFJC/iot_ws/robot0/'
transport="mqtt" # "picoros" or "mqtt"

with open(password_file) as f:
    password = f.read().strip()
    




scheduler = Scheduler()
print('Scheduler')
wifi = WiFiManager(ssid=ssid,password=password) # Ejemplo  Change to your WiFi
node = Node(prefix=prefix,node_name=node_name)

if transport=="picoros":
    socket_client = SocketClient(host=TCP_host, port=TCP_port,scheduler=scheduler, period_ms=100) #192.168.1.100  # Change to the Broker IP
    PubSubTCP(node=node,socket_client=socket_client, prefix=prefix, noecho_name="PubSubTCP")

if transport=="mqtt":        
    PubSubMQTT(client_id=node_name, broker=MQTT_broker,  scheduler=scheduler, node=node, period_ms=100 , 
         prefix=prefix)

DummyLocalPubSubChain(scheduler=scheduler, pubsub=node, n_chain=1, period_ms=800)
WatchdogTask(scheduler=scheduler, pubsub=node, wifi=wifi, period_ms=900)

FollowLineControl(pubsub=node)
CameraSimulator(scheduler=scheduler, pubsub=node, width=40, height=30, period_ms=1000)

#Arm(scheduler=self.scheduler, pubsub=self.pubsub,joint_state={"shoulder": 10, "elbow": 20, "wrist": 30})
#print('Arm')
CarSimulator(scheduler=scheduler, pubsub=node,twist = {"linear": 0.0,"angular": 0.01} , period_ms=1000)
print('Initialized')


scheduler.run()


# =========================================================
# ENTRY POINT
# =========================================================

