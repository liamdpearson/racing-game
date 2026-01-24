import socket


class Network:
    def __init__(self, server, init_data):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server
        self.port = 5555
        self.addr = (self.server, self.port)
        
        self.p_data = self.connect(init_data)
        
        self.all_data = None
        
    def getData(self):
        return self.p_data
   
    def connect(self, init_data):
        try:
            self.client.connect(self.addr)

            self.client.send(str.encode(init_data))
            
            return self.client.recv(2048).decode()
        except:
            pass
        
    def update(self):
        try:
            self.client.send(str.encode(self.p_data))
            self.all_data = self.client.recv(2048).decode()
        except socket.error as e:
            print(e)

    def send(self, data):
        self.client.send(str.encode(data))
    
    def recv(self):
        return self.client.recv(2048).decode()
