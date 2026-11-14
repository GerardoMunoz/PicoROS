OV7670_GPIOs={
    'shutdown' : 0,
    'reset'    : 1,
    'data_0'   : 2,   # D0-D7: GP2 a GP9
    'mclk'     : 10,
    'pclk'     : 11,
    'href'     : 12,
    'vsync'    : 13,
    'sda1'     : 14, #SDA1
    'scl1'     : 15  #SCL1    
    }
SDA1_GPIO=OV7670_GPIOs['sda1']
SCL1_GPIO=OV7670_GPIOs['scl1']
MOTOR4_GPIO=16
MOTOR3_GPIO=17
MOTOR2_GPIO=18
MOTOR1_GPIO=19
SDA0_GPIO=20
SCL0_GPIO=21
IR_GPIO=22
SERVO1_GPIO=26
SERVO2_GPIO=27
VBAT_GPIO=28