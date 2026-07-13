import math
class FollowLineControl:
    def __init__(self,  pubsub):
        self.pubsub = pubsub
        pubsub.subscribe("camera/frame",self.handle_message )
        self.threshold=2000
        self.angular_default=10*math.pi/180



    def handle_message(self, topic, msg):
        #prnt("FollowLineControl.handle_message()",max,msg)
           
        w=msg['w']
        h=msg['h']
        cols=self.column_intensity_fast(msg["frame"], w, h)
        max_cols=max(cols)
        #prnt('FollowLineControl.max_cols',max_cols,self.threshold)
        if max_cols>self.threshold:
            index=cols.index(max_cols)
            angular=self.angular_default*(index / w*2-1)
            #prnt('FollowLineControl.angular True',angular,max_cols,index ,w)        
        else:
            angular=self.angular_default
            #prnt('FollowLineControl.angular False',angular)
        #print('FollowLineControl',angular,index)        
            
        self.pubsub.publish(
            "car/twist",
            {"angular": angular}
        )
        
            
        
            
    def column_intensity_fast(self,b64_data, width, height):
        import ubinascii

        buf = ubinascii.a2b_base64(b64_data)
        cols = [0] * width
        #inc=1/height/3
        x = 0
        for i in range(0, len(buf), 2):
            rgb565 = (buf[i] << 8) | buf[i+1]

            cols[x] += ((rgb565 >> 11) & 0x1F) \
                     + ((rgb565 >> 5) & 0x3F) \
                     + (rgb565 & 0x1F)

            x = (x+1)%width
            
        return cols
