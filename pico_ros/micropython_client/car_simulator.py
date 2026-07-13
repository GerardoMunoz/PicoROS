import time
import math

from task import Task


class CarSimulator(Task):
    def __init__(self, scheduler, pubsub, twist , period_ms=1000):
        super().__init__(scheduler, period_ms)
        self.pubsub = pubsub
        self.twist = twist
        pubsub.subscribe("car/twist",self.handle_message )
        self.angle=45*math.pi/180
        self.time=time.time()
        
        
        

    def update(self):
        actual_time=time.time()
        #prnt('CarSimulator.twist["angular"]',self.twist["angular"],actual_time-self.time)
        self.angle = (self.angle + self.twist["angular"]*(actual_time-self.time))
        #prnt("angulo0",self.angle,math.pi)
        while self.angle > math.pi:
            self.angle -= 2*math.pi
        #prnt("angulo1",self.angle)
        while self.angle < -math.pi:
            self.angle += 2*math.pi
        #prnt("angulo2",self.angle)

        self.time=actual_time
        self.pubsub.publish(
            "car/state",
            {"angle": self.angle}
        )
        #prnt("angulo3",self.angle)
 #             self.pubsub.publish(
#                 "car/twist",
#                 {"Twist": str(twist)}
#             )
#            print("Car.update()",self.twist)

    def handle_message(self, topic, msg):
           #prnt("Car.handle_message()",msg)
           self.twist.update(msg)
