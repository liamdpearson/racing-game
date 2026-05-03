# Liam Pearson
# Multiplayer Racing Game Server


import socket
from _thread import *
import time



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
    s = " ".join(i for i in lis)
    return s

    

def convert_pos(lis):
    s = " ".join(make_pos(i) for i in lis)
    return s

    
    
    
def main(map_index):


    start_coords = { 0: (300,2580,8500), 1: (3150,1900,4300), 2: (500,5075,5200)}

    server = get_local_ipv4()
    port = 5555
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        s.bind((server, port))
    except socket.error as e:
        str(e)
    
    s.listen()
    s.settimeout(1)
    print("Waiting for a connection, Server Started")
    finished_players = ""
    checkpoint_data = []
    all_init_data = []
    started = False
    player_refs = []
    all_finished = False
    host_left = False

    pos = []
    def threaded_client(conn, player_ref):
        nonlocal connected_players, all_finished, host_left
        player = player_ref[0]

        def lobby_loop(data):
            player = player_ref[0]
            nonlocal started
            if data == "start":
                started = True
                nonlocal players_in_game
                players_in_game = connected_players


            reply = make_pos(pos[player]) + "|" + str(player) + " " + lis_to_str(all_init_data)

            if started == True:
                reply += "start"
            
            conn.send(str.encode(reply))
        

        def game_loop(data):
            player = player_ref[0]
            pos[player] = data[:-1] # excludes int for sorting
            checkpoint_data[player] = data[-1] # int for sorting
            nonlocal finished_players, all_finished

            if checkpoint_data[player] >= start_coords[map_index][2]:
                if str(player) not in finished_players:
                    finished_players += str(player)

            players_ahead = 0
            for i in checkpoint_data:
                if i > checkpoint_data[player]:
                    players_ahead += 1   

            reply = convert_pos(pos) + str(1+players_ahead)

            if len(finished_players) == connected_players:
                all_finished = True

            if all_finished:
                reply = reply + " " + finished_players + "f"
            #print("Received: ", data)
            #print("Sending: ", reply)
            conn.sendall(str.encode(reply))



        all_init_data.append(conn.recv(2048).decode())

        conn.send(str.encode(make_pos(pos[player])))

        while True:

            start = time.time()


            try:
                data = conn.recv(2048).decode()
                if not data:
                    print("Disconnected")
                    break
                
                if data == " " or data == "start":
                    lobby_loop(data)
                else:
                    game_loop(read_pos(data))
            except socket.error as e:
                print(f"Socket error occurred: {e}")
                break
            
            if host_left:
                break
                
            time.sleep(max(0, 1/60 - (time.time() - start)))
        
        leaving_player = player_ref[0]
        if leaving_player == 0:
            host_left = True

        if started == False:
            pos.pop(leaving_player)
            checkpoint_data.pop(leaving_player)
            all_init_data.pop(leaving_player)
            player_refs.pop(leaving_player)

            for ref in player_refs:
                if ref[0] > leaving_player:
                    ref[0] -= 1

            for i in range(len(pos)):
                pos[i] = (start_coords[map_index][0]+75*i, start_coords[map_index][1], 0)
            
        
        print("Player " + str(player_ref[0]+1) + " disconnected")
        connected_players -= 1
        conn.close()
    
    players_in_game = 0
    connected_players = 0
    while not started and not host_left:
        try:
            if connected_players < 5:
                conn, addr = s.accept()
                print("Connected to ", addr)

                data = start_coords[map_index]
                pos.append((data[0]+75*connected_players, data[1], 0, 0, 0, 0))
                checkpoint_data.append(0)

                player_ref = [connected_players]
                player_refs.append(player_ref)

                start_new_thread(threaded_client, (conn, player_ref))
                connected_players += 1

        except socket.timeout:
            pass