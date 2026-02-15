import socket
from _thread import *



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
    s.settimeout(1)
    print("Waiting for a connection, Server Started")
    finished_players = ""
    checkpoint_data = []
    all_init_data = []
    started = False
    player_refs = []

    # x, y, head_angle, legs_angle, anim_index, char_index
    pos = []
    def threaded_client(conn, player_ref):
        nonlocal connected_players
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
            nonlocal finished_players

            if checkpoint_data[player] >= 8500:
                if str(player) not in finished_players:
                    finished_players += str(player)

            players_ahead = 0
            for i in checkpoint_data:
                if i > checkpoint_data[player]:
                    players_ahead += 1   

            reply = convert_pos(pos) + str(1+players_ahead)

            if len(finished_players) == players_in_game:
                reply = reply + " " + finished_players + "f"
            #print("Received: ", data)
            #print("Sending: ", reply)
            conn.sendall(str.encode(reply))



        all_init_data.append(conn.recv(2048).decode())

        conn.send(str.encode(make_pos(pos[player])))

        while True:
            try:
                data = conn.recv(2048).decode()
                if not data:
                    print("Disconnected")
                    break
                
                if data == " " or data == "start":
                    lobby_loop(data)
                else:
                    game_loop(read_pos(data))
            except:
                break

        if started == False:
            leaving_player = player_ref[0]

            pos.pop(leaving_player)
            checkpoint_data.pop(leaving_player)
            all_init_data.pop(leaving_player)
            player_refs.pop(leaving_player)

            for ref in player_refs:
                if ref[0] > leaving_player:
                    ref[0] -= 1

            for i in range(len(pos)):
                pos[i] = (300+75*i,2580,0)
            
        

        connected_players -= 1
        conn.close()
    
    players_in_game = 0
    connected_players = 0
    while True:
        try:
            if connected_players < 5:
                conn, addr = s.accept()
                print("Connected to ", addr)

                pos.append((300+75*connected_players,2580,0))
                checkpoint_data.append(0)

                player_ref = [connected_players]
                player_refs.append(player_ref)

                start_new_thread(threaded_client, (conn, player_ref))
                connected_players += 1

        except socket.timeout:
            pass
            
        if started == True and connected_players == 0:
            print("Closed server")
            break
        

        
        
        
if __name__ == "__main__":
    main()