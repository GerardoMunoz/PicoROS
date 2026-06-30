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

class MainApp:
    def __init__(self,ssid,password,host,port):

        self.scheduler = Scheduler()
        print('Scheduler')
        self.wifi = WiFiManager(ssid=ssid,password=password) # Ejemplo  Change to your WiFi
        #self.wifi.connect()
        print('WiFiManager')
        self.socket_client = SocketClient(host=host, port=port,scheduler=self.scheduler) #192.168.1.100  # Change to the Broker IP
        #self.socket_client.connect()
        print('SocketClient')
        #self.pubsub = Node(self.socket_client, prefix='UDFJC/emb1/robot0/')
        self.pubsub = Node(prefix='UDFJC/emb1/robot0/',node_name='emb_node')
        PubSubTCP(node=self.pubsub,socket_client=self.socket_client, prefix='UDFJC/emb1/robot0/', noecho_name="PubSubTCP")
        print('Node')

        DummyLocalPubSubChain(scheduler=self.scheduler, pubsub=self.pubsub, n_chain=1, period_ms=800)
        WatchdogTask(scheduler=self.scheduler, pubsub=self.pubsub, wifi=self.wifi, period_ms=900)
        print('WatchdogTask')
        FollowLineControl(pubsub=self.pubsub)
        CameraSimulator(scheduler=self.scheduler, pubsub=self.pubsub, width=40, height=30, period_ms=1000)
        print('CameraPublisherTask')
        #Arm(scheduler=self.scheduler, pubsub=self.pubsub,joint_state={"shoulder": 10, "elbow": 20, "wrist": 30})
        #print('Arm')
        CarSimulator(scheduler=self.scheduler, pubsub=self.pubsub,twist = {"linear": 0.0,"angular": 0.01} )
        print('Car')
 

    def run(self):
        self.scheduler.run()


# =========================================================
# ENTRY POINT
# =========================================================

ssid="PEREZ"
password_file=".env"
host="192.168.1.17"
port=5051

with open(password_file) as f:
    password = f.read().strip()

app = MainApp(ssid=ssid,password =password,host=host,port=port)
app.run()