import ubinascii
import math

import util
from task import Task

class CameraSimulator(Task):
    # Upgrade to the real ov7670 camera, it could read the data on the other `_thread`
    def __init__(self, scheduler, pubsub, width=40, height=30, period_ms=20000):
        super().__init__(scheduler, period_ms)
        #print('Camera1')
        self.pubsub = pubsub
        self.WIDTH = width
        self.HEIGHT = height
        self.buf = bytearray(width * height * 2)
        #print('Camera2')
        self.car_angle=0
        self.line_angle=60
        pubsub.subscribe("car/state",self.handle_message_car )
        pubsub.subscribe("stick/state",self.handle_message_line )
        self.sended=0

#        self.last = 0
#        self.interval = 2

    def angle_to_pixel(self,car_angle, line_angle, width, fov=60):
        # relative angle
        delta = (line_angle - car_angle)*180/math.pi
        # normalize to [-180, 180]
        while delta > 180:
            delta -= 360
        while delta < -180:
            delta += 360

        # if outside camera view → not visible
        #if abs(delta) > fov / 2:
        #    return None  # line not in frame

        # map to pixel
        x = int((delta / fov + 0.5) * width)

        # clamp (safety)
        if x < 0:
            x = 0
        elif x >= width:
            x = width - 1
        #prnt('angle_to_pixel.delta',delta,x, fov , width)

        return x


    def pixel_to_angle(self, car_angle, x, width, fov=60):
        # normalized column → [-0.5, 0.5]
        norm = x / width - 0.5

        # angle relative to camera center (degrees)
        delta = norm * fov

        # convert to radians
        delta_rad = delta * math.pi / 180

        # absolute angle in world
        angle = car_angle + delta_rad

        return angle

    def update(self):
        #now = time.time()

        #if now - self.last > self.interval:
#            gc.collect()
            self.sended+=1

            frame = self._generate_frame(control_line="angle")
#            frame_b64 = ubinascii.b2a_base64(frame).decode().strip()
            frame_b64 = ubinascii.b2a_base64(frame).decode().replace("\n", "")

            self.pubsub.publish(
                "camera/frame",
                {
                    "first_ts":  util.time_float(),
                    "sended": self.sended,
                    "w": self.WIDTH,
                    "h": self.HEIGHT,
                    "frame": frame_b64
                }
            )

            #prnt("📤 Frame")
            #self.last = now

    def handle_message_car(self, topic, msg):
           #prnt("Camera.handle_message_car()",msg)
           self.car_angle=msg["angle"]

    def handle_message_line(self, topic, msg):
           self.line_angle=msg["angle"]
           print("Camera.handle_message_line()",msg,self.line_angle)


    def _generate_frame(self,control_line="time"):
        if control_line=="angle":
            t = self.angle_to_pixel(self.car_angle, self.line_angle, self.WIDTH, fov=60)
            #print('Camera._generate_frame.angle',t,self.car_angle, self.line_angle)
        else:
            t = int(time.time()*4) % self.WIDTH
        #prnt('_generate_frame.t',t,control_line)
        for i in range(0, len(self.buf), 2):
            x=(i//2)%(self.WIDTH)
            y=(i//2)//(self.WIDTH)
            if abs(x-t)<=3:
                r=int(255*(1-abs(x-t)/3))
                g=r
                b=r
            else:
                #gb=0

                car_angle=self.car_angle
                while car_angle > math.pi:
                    car_angle -= 2*math.pi
                #prnt("angulo1",self.angle)
                while car_angle < -math.pi:
                    car_angle += 2*math.pi
                #background = ((i//2)%(self.WIDTH))*256//self.WIDTH#(i * 10) % 256
                pixel_angle=self.pixel_to_angle( car_angle, x, self.WIDTH, fov=60)
                #background = int(pixel_angle*255/(2*math.pi)+math.pi)
                #print('background',background,car_angle)
                ang=15
                alt=5            
                r = (int((y//alt)*170+((pixel_angle*180/math.pi)//ang)*320)%255)#*background
                g = (int((y//alt)*230+((pixel_angle*180/math.pi)//ang)*290)%255)#min(gb*127+int((pixel_angle*18/math.pi)%2*64),255)#(128 + i * 15) % 256
                b = (int((y//alt)*370+((pixel_angle*180/math.pi)//ang)*190)%255)#gb*255#(255 - i * 35) % 256

            color = self.rgb565(r, g, b)
            hi = (color >> 8) & 0xFF
            lo = color & 0xFF
            self.buf[i] = hi
            self.buf[i + 1] = lo

        return self.buf

    def rgb565(self, r, g, b):
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
