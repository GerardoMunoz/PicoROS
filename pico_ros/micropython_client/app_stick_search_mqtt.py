from dummy_local_pubsub_chain import DummyLocalPubSubChain
from watchdog_task import WatchdogTask
from follow_line_control import FollowLineControl
from camera_simulator import CameraSimulator
from car_simulator import CarSimulator
from scheduler import Scheduler
from wifi_manager import WiFiManager
#from socket_client import SocketClient
from node import Node
from pubsub_mqtt import PubSubMQTT



ssid="Ejemplo"
password_file=".env"
TCP_host="192.168.0.101"
TCP_port=5051
MQTT_broker="192.168.0.101"
node_name='emb_node_0'

with open(password_file) as f:
    password = f.read().strip()



scheduler = Scheduler()
print('Scheduler')
wifi = WiFiManager(ssid=ssid,password=password) # Ejemplo  Change to your WiFi
#self.wifi.connect()
print('WiFiManager')
#self.socket_client = SocketClient(host=host, port=port,scheduler=self.scheduler) #192.168.1.100  # Change to the Broker IP
#self.socket_client.connect()
#print('SocketClient')
#self.pubsub = Node(self.socket_client, prefix='UDFJC/emb1/robot0/')
node = Node(prefix='UDFJC/emb1/robot0/',node_name=node_name)
PubSubMQTT(client_id=node_name, broker=MQTT_broker,  scheduler=scheduler, node=node, period_ms=100 , 
         prefix="UDFJC/emb1/robot0/")
print('Node')

DummyLocalPubSubChain(scheduler=scheduler, pubsub=node, n_chain=1, period_ms=800)
WatchdogTask(scheduler=scheduler, pubsub=node, wifi=wifi, period_ms=900)
print('WatchdogTask')
FollowLineControl(pubsub=node)
CameraSimulator(scheduler=scheduler, pubsub=node, width=40, height=30, period_ms=1000)
print('CameraPublisherTask')
#Arm(scheduler=self.scheduler, pubsub=self.pubsub,joint_state={"shoulder": 10, "elbow": 20, "wrist": 30})
#print('Arm')
CarSimulator(scheduler=scheduler, pubsub=node,twist = {"linear": 0.0,"angular": 0.01} )
print('Car')


scheduler.run()


# =========================================================
# ENTRY POINT
# =========================================================

