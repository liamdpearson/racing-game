import socket
from _thread import *
import sys



def get_local_ipv4():
    try:
        # Get the local hostname
        host_name = socket.gethostname()
        # Resolve the hostname to an IPv4 address
        ip_address = socket.gethostbyname(host_name)
        return ip_address
    except socket.gaierror:
        return "Could not resolve hostname"
    except Exception as e:
        return f"An error occurred: {e}"
    
    
    
def read_pos(stra):
    
    stra = stra.split(",")
    f_tup = []
    for i in stra:
        f_tup.append(int(float(i))) 
    tup = tuple(f_tup)
    
    return tup



def make_pos(tup):
    
    stra = str(tup[0])
    for i in range(1, len(tup)):
        stra = stra + "," + str(tup[i])
    
    return stra

def lis_to_str(lis):
    s = ""
    for i in lis:
        s = s + i + " "
    return s

def convert_pos(lis):
    s = ""
    for i in lis:
        s = s + make_pos(i) + " "
    return s

    
    
    
def main():
    server = get_local_ipv4()
    port = 5555
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        s.bind((server, port))
    except socket.error as e:
        str(e)
    
    s.listen()
    print("Waiting for a connection, Server Started")
    finished_players = []
    checkpoint_data = []
    all_init_data = []
    started = False
    # x, y, head_angle, legs_angle, anim_index, char_index
    pos = []
    def threaded_client(conn, player):

        def lobby_loop():
            nonlocal started
            while started == False:
                conn.send(str.encode(str(player) + " " + lis_to_str(all_init_data)))
                try:
                    data = conn.recv(2048).decode() # wait for client to recive data before sending again
                    if data == "start":
                        started = True
                        conn.send(str.encode(str(player) + " " + lis_to_str(all_init_data)+"start"))
                        game_loop()
                        break
                except:
                    break
        
            
        
        def game_loop():
            reply = ""
            while True:
                try:
                    data = read_pos(conn.recv(2048).decode())
                    pos[player] = data[:-1] # excludes int for sorting
                    checkpoint_data[player] = data[-1] # int for sorting

                    if checkpoint_data[player] >= 8500:
                        if player not in finished_players:
                            finished_players.append(player)
                            if len(finished_players) == currentPlayer:
                                s = ""
                                for i in finished_players:
                                    s = s + str(i)
                                conn.send(str.encode("f"+s))
                                lobby_loop()
                                break

                    players_ahead = 0
                    for i in checkpoint_data:
                        if i > checkpoint_data[player]:
                            players_ahead += 1

                    

                    
                    if not data:
                        print("Disconnected")
                        break
                    else:
                        reply = convert_pos(pos) + str(1+players_ahead)
                            
                        #print("Received: ", data)
                        #print("Sending: ", reply)
                    conn.sendall(str.encode(reply))
                except:
                    break

        all_init_data.append(str(player) + conn.recv(2048).decode())

        conn.send(str.encode(make_pos(pos[player])))

        lobby_loop()
        
            
        print("Lost connection")
        conn.close()
    
    currentPlayer = 0
    while currentPlayer < 5:
        conn, addr = s.accept()
        print("Connected to ", addr)

        pos.append((300+75*currentPlayer,2580,0))
        checkpoint_data.append(0)
        start_new_thread(threaded_client, (conn, currentPlayer))
        currentPlayer += 1
        
if __name__ == "__main__":
    main()