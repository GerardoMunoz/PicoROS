import rp2
from machine import Pin

from pico_ros.task import Task
from pico_ros.ring_buffer import RingBuffer

class IRIn(Task):

    END = 0
    
    @rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
    def count1():

        # =====================================================
        # Y = on threshold
        # =====================================================

        pull(block)
        mov(y, osr)

        # =====================================================
        # Estado inicial
        # =====================================================

        jmp(pin, "on_off")

        # =====================================================
        # on
        # =====================================================

        label("off_on")

        mov(x, y)

        label("on_LOOP")

        # -----------------------------------------------------
        # Decrementamos X
        # -----------------------------------------------------

        jmp(x_dec, "on_DUMMY") #1

        
        # -----------------------------------------------------
        # Permanecemos en on hasta que aparezca off
        # -----------------------------------------------------

        label("on_SLEEP")

        jmp(pin, "on_off")
        jmp("on_SLEEP")


        # -----------------------------------------------------
        # on todavía no terminó
        # -----------------------------------------------------

        label("on_DUMMY") 

        # ¿Terminó on porque apareció off?
        jmp(pin, "on_END") #2

        # Padding
        nop()[6]           #3

        jmp("on_LOOP")     #4


        # -----------------------------------------------------
        # on ya terminó
        # -----------------------------------------------------

        label("on_END")

        #mov(isr, invert(x))#
        #push(noblock)
        #irq(rel(0))

        jmp("on_off")


        # =====================================================
        # on → off
        # =====================================================

        label("on_off")

        # X = ON_THRESHOLD_US
        mov(x, y)


        # =====================================================
        # off
        # =====================================================

        label("off_LOOP")

        # Mientras siga off seguimos contando
        jmp(x_dec, "off_DUMMY") #1

        mov(isr, null)
        push(noblock)
        irq(rel(0))

        # Si pasa on_THRESHOLD_US esperamos el cero

        label("off_SLEEP")
        jmp(pin,"off_SLEEP")
        jmp("off_on")

        label("off_DUMMY")

        nop()[7]             #2

        # ¿Seguimos off?
        jmp(pin, "off_LOOP")  #3


        # -----------------------------------------------------
        # off → on
        #
        # X contiene el contador restante.
        # -----------------------------------------------------

        mov(isr, x)#
        push(noblock)
        irq(rel(0))
        jmp("off_on")
        

    def __init__(
        self,
        scheduler,
        pubsub,
        pin_ir,
        sm=0,
        off0_threshold_us=1100,
        off1_threshold_us=3000,
        on_threshold_us=20000,
        pio_freq=10_000_000,
        min_bits=8
    ):
        """
        IR receiver driver.

        PIO events:

            positive  -> ON duration
            negative  -> OFF duration
            0         -> END OF FRAME

        The code is constructed using only OFF durations.

        OFF < off0_threshold_us
            -> bit 0

        OFF >= off0_threshold_us
            -> bit 1
        """
        self.pubsub=pubsub
        super().__init__(scheduler, period_ms=100)

        self.off0_threshold_us = off0_threshold_us
        self.off1_threshold_us = off1_threshold_us
        self.on_threshold_us = on_threshold_us
        self.min_bits=min_bits

        #self.new_code = False
        self.code = 0
        self.n_bits = 0
        self.rb=RingBuffer(size=10, unit="ir_code", tag="ir_sensor", warn_full=True)

        self.sm = rp2.StateMachine(
            sm,
            self.count1,
            freq=pio_freq,
            jmp_pin=Pin(pin_ir, Pin.IN, Pin.PULL_UP)
        )
        self.sm.irq(handler=self._irq_handler)

        self.sm.active(1)

        # Threshold used by the PIO to detect END.
        self.sm.put(on_threshold_us)


    def _irq_handler(self, sm):

        while sm.rx_fifo():

            raw = sm.get()

            if raw == 0:
                # END
                if self.n_bits >= self.min_bits:
                    self.rb.append(self.code)
                    #print('raw == 0',self.code,self.n_bits)
                #self.rb.append((self.code, self.n_bits))
                
                #self.last_code = self.code
                #self.last_bits = self.n_bits

                self.code = 0
                self.n_bits = 0 #for_debug

                #self.new_code = True
                continue

            elif raw & 0x8000_0000:
                continue
            else:
                value = self.on_threshold_us-raw
                if 0<value < self.off0_threshold_us:
                    bit = 0

                elif value < self.off1_threshold_us:
                    bit = 1
                else:
                    #print('IRIn._irq_handler Valor fuera de rango',raw,value,self.code,self.n_bits)
                    continue
                
                self.code = (self.code << 1) | bit
                self.n_bits += 1
                
             
                
 
            
    def update(self):
        #print('.',end='')

        if len(self.rb)==0:
            return

        msg = {"values":self.rb.pop_all()}
        #bits = self.last_bits

        #self.new_code = False

        # Publicar aquí
        self.pubsub.publish("IRIn/value",msg)
        print("IRIn/value:",msg)




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

    ir = IRIn(
        scheduler=scheduler,
        pubsub=node,
        pin_ir=config_gpio.IR_GPIO,
    )
    
#     def handle_ir_reader_value(topic, msg):
#         print("handle_ir_reader_value",msg)
#     node.subscribe("IRIn/value",handle_ir_reader_value )
            


    scheduler.run()




