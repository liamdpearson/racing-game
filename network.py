import socket


class Network:
    def __init__(self, init_data):
        self.init_data = init_data
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = ""
        self.port = 5555
        self.addr = ("", self.port)
        
        self.p_data = ""
        
        self.all_data = None
        
    def getData(self):
        return self.p_data
    
    def set_server(self, server):
        self.server = server
        self.addr = (server, self.port)
   
    def connect(self):
        try:
            self.client.connect(self.addr)

            self.client.send(str.encode(self.init_data))
            
            self.p_data = self.client.recv(2048).decode()
            return True
        except:
            return False
        
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
