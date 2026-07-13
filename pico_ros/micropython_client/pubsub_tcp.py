import json

import util

class PubSubTCP:
    def __init__(self, node,socket_client, prefix='UDFJC/emb1/robot0/', noecho_name=None):
        self.sock = socket_client
        self.sock.add_action("PUB", self.handle_pub)
        self.sock.add_action("SUB", self.handle_sub)
        self.prefix=prefix
        self.noecho_name  = noecho_name or self.__class__.__name__
        self.node=node
        node.add_transport(self)

            
    def new_sub(self,msg):
        self.sock.ensure()
        self.sock.send_json(msg)


    def publish(self, topic, data):
        ts=util.time_float()
        self.sock.ensure()

        pkt = {
            "action": "PUB",
            "topic": self.prefix+topic,
            "data": data,
            "ts_node":ts
        }

        self.sock.send_json(pkt)




    def subscribe(self, topic ):#topic without prefix
        #self.subscriptions.setdefault(topic, set()).add(callback)
        self.sock.ensure()

        pkt = {
            "action": "SUB",
            "topic": self.prefix+topic,
        }
        self.sock.send_json(pkt)
        print(f"[INFOPubSubTCP] [] [SUB ] : [{topic}]")

    def handle_pub(self, msg):
        topic = msg['topic']
        print('Node.handle_pub', topic)
        if not topic.startswith(self.prefix):
            print(ignored)
            return  # ignore чужое

        local_topic = topic[len(self.prefix):]
        print('Node.handle_pub', local_topic)
        

        self.node.publish(local_topic, msg['data'])

    def handle_sub(self,msg):
        print('Node.handle_sub ignored',msg)

