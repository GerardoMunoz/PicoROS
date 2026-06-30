from task import Task



class DummyLocalPubSubChain(Task):
    def __init__(self, scheduler, pubsub, n_chain, period_ms=1000):
        super().__init__(scheduler, period_ms)
        self.pubsub = pubsub
        self.n_chain=n_chain
        self.name='LocalPubSubChain_'+str(n_chain)
        self.topic_name="dummy/chain_"
        for i in range(n_chain):
            pubsub.subscribe(self.topic_name+str(i),self.handle_dummy_chain )

    def update(self):
            self.pubsub.publish(
                self.topic_name+'0',
                { 'index':0 }
            )
            
    def handle_dummy_chain(self, topic, msg):
            index=msg['index']+1
            self.pubsub.publish(
                self.topic_name+str(index),
                { 'index':index }
            )
