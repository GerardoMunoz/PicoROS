from drivers.ov7670_wrapper import OV7670Wrapper
from machine import Pin, I2C, SPI, PWM
import gc
import sys

from pico_ros.task import Task



OV7670_SIZE_DIV1  = 0 # 640x480
OV7670_SIZE_DIV2  = 1 # 320x240
OV7670_SIZE_DIV4  = 2 # 160x120
OV7670_SIZE_DIV8  = 3 # 80x60
OV7670_SIZE_DIV16 = 4 # 40x30

OV7670_TEST_PATTERN_NONE           = 0
OV7670_TEST_PATTERN_SHIFTING_1     = 1
OV7670_TEST_PATTERN_COLOR_BAR      = 2
OV7670_TEST_PATTERN_COLOR_BAR_FADE = 3

SIZE_DIV=OV7670_SIZE_DIV4


class Camera(Task):
    def __init__(self, pins, i2c, scheduler, pubsub,  period_ms=10000, test=OV7670_TEST_PATTERN_NONE):
        super().__init__(scheduler, period_ms)
        self.pubsub = pubsub
        # ---------- 1) GENERAR XCLK CON PWM PARA LA CÁMARA ----------
        print(f"Configurando MCLK para OV7670 en {pins['mclk']}...")
        pwm = PWM(Pin(pins['mclk']))
        pwm.freq(30_000_000)
        pwm.duty_u16(32768)

        try:
            self.ov7670 = OV7670Wrapper(
                i2c_bus=i2c,
                mclk_pin_no=pins['mclk'],
                pclk_pin_no=pins['pclk'],
                data_pin_base=pins['data_0'],#data_(i+1)=data_(i)+1
                vsync_pin_no=pins['vsync'],
                href_pin_no=pins['href'],
                reset_pin_no=pins['reset'],
                shutdown_pin_no=pins['shutdown'],
            )
            self.ov7670.wrapper_configure_rgb()
            IMAGE_FORMAT = "rgb565"

            #ov7670.wrapper_configure_yuv()
            
            self.ov7670.wrapper_configure_base()

            width, height = self.ov7670.wrapper_configure_size(SIZE_DIV)
            self.ov7670.wrapper_configure_test_pattern(test)
            print(f"✅ OV7670 inicializada. Resolución: {width}x{height}")

            self.TOPIC_FORMAT = IMAGE_FORMAT+"_"+str(width)+"x"+str(height)


            self.frame_buf = bytearray(width * height * 2)
            gc.collect()

        except Exception as e:
            print(f"❌ Error al inicializar la cámara OV7670: {e}")
            sys.exit(1)



    def update(self):
        self.ov7670.capture(self.frame_buf)
        self.pubsub.publish(
            "camera/frame/"+self.TOPIC_FORMAT,
            memoryview(self.frame_buf)
        )






















if __name__ == "__main__":
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


    print("Inicializando I2C y OV7670...")
    pins=config_gpio.OV7670_GPIOs
    i2c1 = I2C(1, freq=400_000, scl=Pin(pins['scl1']), sda=Pin(pins['sda1']))
    camera=Camera(pins=pins, i2c=i2c1, scheduler=scheduler, pubsub=node, period_ms=1000, test=OV7670_TEST_PATTERN_COLOR_BAR)



    scheduler.run()

