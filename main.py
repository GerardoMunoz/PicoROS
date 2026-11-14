from pico_ros.watchdog_task import WatchdogTask
from pico_ros.scheduler import Scheduler
from pico_ros.wifi_manager import WiFiManager
from pico_ros.node import Node
from pico_ros.pubsub_mqtt import PubSubMQTT

import config_wifi
import config_mqtt
import config_gpio

# SSID="Ejemplo" #  Change to your WiFi
# PSW_FILE=".env" # File name with password
# MQTT_BROKER="broker.hivemq.com"
# NODE_NAME='emb_node_0'
# PREFIX='UDFJC/iot_ws/robot0/'
# 
# with open(PSW_FILE) as f:
#     password = f.read().strip()

scheduler = Scheduler()
print('Scheduler')
wifi = WiFiManager(ssid=config_wifi.SSID, password=config_wifi.PASSWORD) 
node = Node(prefix=config_mqtt.PREFIX, node_name=config_mqtt.NODE_NAME)
PubSubMQTT(client_id=config_mqtt.NODE_NAME, broker=config_mqtt.MQTT_BROKER,  scheduler=scheduler, node=node, period_ms=100, prefix=config_mqtt.PREFIX)
WatchdogTask(scheduler=scheduler, pubsub=node, wifi=wifi, period_ms=9000)
print('Initialized')


scheduler.run()



