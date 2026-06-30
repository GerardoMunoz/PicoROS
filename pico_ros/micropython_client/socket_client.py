import usocket as socket
import json

from task import Task


class SocketClient(Task):
    def __init__(self, host, port, scheduler, period_ms=100):
        super().__init__(scheduler, period_ms)
        self.host = host
        self.port = port
        self.sock = None
        self.actions = {}
        self._rx_buffer = b""
        self.connect()

    def connect(self):
        print("🔌 Conectando al broker...")
        addr = socket.getaddrinfo(self.host, self.port)[0][-1]
        #prnt('addr',addr)
        self.sock = socket.socket()
        #prnt('sock',self.sock)
        self.sock.connect(addr)
        #prnt('sock.connect')
        #self.sock.settimeout(0.1)
        self.sock.setblocking(False)
        print("✅ Conectado")

    def ensure(self):
        if self.sock is None:
            self.connect()

    def send(self, data):
        total = 0
        while total < len(data):
            try:
                sent = self.sock.send(data[total:])
                if sent == 0:
                    print("⚠️ Socket closed")
                    return False
                total += sent
            except OSError:
                print("⚠️ Socket send except")
                # Socket not ready → exit and retry later
                return False
        return True


    def send_json(self, obj):
        self.send((json.dumps(obj) + "\n").encode())

    def close(self):
        try:
            if self.sock:
                self.sock.close()
        except:
            pass
        self.sock = None



    def recv_json_nonblocking(self):
        messages = []

        try:
            data = self.sock.recv(1024)

            if data == b'':
                print("⚠️ Connection closed by peer")
                self.close()
                return []

            if data:
                self._rx_buffer += data

        except OSError:
            # No data available (non-blocking)
            return []

        while b"\n" in self._rx_buffer:
            line, self._rx_buffer = self._rx_buffer.split(b"\n", 1)

            if not line:
                continue

            try:
                messages.append(json.loads(line))
            except Exception as e:
                print("JSON error:", e)
                print("Bad line:", line)

        return messages



    def update(self):
        msgs = self.recv_json_nonblocking()
        for msg in msgs:
            action = msg.get("action")
            if action in self.actions:
                #print("Socket",msg)
                self.actions[action](msg)
        
    def add_action(self, action, callback):
        self.actions[action] = callback        
