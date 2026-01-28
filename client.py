# Liam Pearson
# Oct 7 2025
# Multiplayer Game Client


import arcade # type: ignore
import arcade.gui # type: ignore
import math
import threading
import socket

from network import Network
import server
import edit_file



SCREEN_WIDTH, SCREEN_HEIGHT = arcade.window_commands.get_display_size()

#SCREEN_WIDTH, SCREEN_HEIGHT = 500, 500


class Game(arcade.View):
    """ Actual Game Function """
    def __init__(self, all_init_data):
        super().__init__()

        self.start_pos = read_pos(self.window.n.getData())
        
        self.player = None
        self.other_players = []

        self.all_init_data = all_init_data.split()
        self.player_index = int(self.all_init_data[0])
        self.players = self.all_init_data[1:]
        self.player_data = self.players[self.player_index]
        self.other_players_data = [player for player in self.players if int(player[0]) != self.player_index]

        self.char_index = int(self.player_data[-1])
        self.name = self.player_data[1:-1]
        
        self.all_positions = None
        
        self.listen_thread = threading.Thread(target=self.listen_for_updates, daemon = True)
        self.listen_thread.start()

        #top speed, acceleration, break_speed, handling
        self.car_stats = ((17, 0.1, 0.2, 2), (16, 0.15, 0.25, 2.25), (16.5, 0.125, 0.225, 2.125))
        
        self.tile_map = None
        self.wall_list = None
        
        self.camera = None
        self.gui_camera = None
        
        self.physics_engine = None

        self.start_counter = 10
        self.locked = True
        self.crossed_finishline = 0
        
        self.setup()
    
    
    
    def setup(self):
        
        # setup map and walls
        self.tile_map = arcade.load_tilemap("maps/map1.json", scaling=3, offset=(0,0))
        self.wall_list = self.tile_map.sprite_lists["Walls"]
        self.floor_list = self.tile_map.sprite_lists["Floor"]
        self.decor_list = self.tile_map.sprite_lists["Decor"]
        self.no_walk_list = self.tile_map.sprite_lists["No Walk"]
        
        
        self.walls_n_railings = self.wall_list
        
        for railing in self.no_walk_list:
            self.walls_n_railings.append(railing)
        
        # pos x, pos y, move speed, anim speed, char index, 
        self.player = Player(self.start_pos[0], self.start_pos[1], self.car_stats[self.char_index], [arcade.key.LSHIFT], self.char_index, self.name)

        for player in self.other_players_data:
            self.other_players.append(OtherPlayer(500, 500, int(player[-1]), player[1:-1]))
        
        # setup cameras
        self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.gui_camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # setup physics engine
        self.physics_engine = arcade.PhysicsEngineSimple(self.player.player_sprite, self.walls_n_railings)
        
        # camera offset
        self.cam_offset_x = SCREEN_WIDTH/2
        self.cam_offset_y = SCREEN_HEIGHT/2
        
    
    
    def listen_for_updates(self):
        while self.window.done == False:
            self.window.n.update()
            #print("listening")
            
        print("listening stopped")
        return None
        
    
        
    def on_draw(self):
        arcade.start_render()
        
        self.camera.use()
        
        self.floor_list.draw(pixelated = True)    
        self.decor_list.draw(pixelated = True)
        self.no_walk_list.draw(pixelated = True)
        self.wall_list.draw(pixelated = True)
        
        
        if self.other_players:
            for player in self.other_players:
                player.draw()
        self.player.draw()
        
        
        # draw gui 
        self.gui_camera.use()
        if self.locked:
            arcade.draw_text(int(self.start_counter), SCREEN_WIDTH/2, 
                             SCREEN_HEIGHT/2, arcade.color.YELLOW,
                             80, anchor_x="center", font_name="Kenney Mini Square")

        
        
    def on_update(self, delta_time):
            
        self.physics_engine.update()
        if self.locked:
            self.start_counter -= delta_time
            if self.start_counter < 0:
                self.locked = False
        else:
            self.player.update(delta_time)
        
        cam_pos_x = self.player.player_sprite.center_x - self.cam_offset_x
        cam_pos_y = self.player.player_sprite.center_y - self.cam_offset_y
        
        self.camera.move_to((cam_pos_x, cam_pos_y))
        
        self.window.n.p_data = make_pos((self.player.player_sprite.center_x,
                                         self.player.player_sprite.center_y,
                                         self.player.player_sprite.angle,
                                         self.crossed_finishline
                                         ))
        
        
        if self.window.n.all_data:
            self.all_positions = self.window.n.all_data.split()
            del self.all_positions[self.player_index]
            if self.all_positions:
                for i in range(len(self.all_positions)):
                    data = read_pos(self.all_positions[i])
                    player = self.other_players[i]
                    player.player_sprite.center_x = data[0]
                    player.player_sprite.center_y = data[1]
                    player.player_sprite.angle = data[2]
        
        #if self.other_players:
            #for player in self.other_players:
                #player.update()
        
    
    
        


    def on_key_press(self, key, modifiers):
        self.player.key_pressed(key, modifiers)
    

    def on_key_release(self, key, modifiers):
        self.player.key_released(key, modifiers)
            
        
    #def on_mouse_motion(self, x, y, dx, dy):
        #self.player.mouse_x, self.player.mouse_y = x-SCREEN_WIDTH/2, y-SCREEN_HEIGHT/2
        




class Player():
    def __init__(self, pos_x, pos_y, car_stats, keybinds, char_index, name):
        super().__init__()
        
        # player variables
        self.char_index = char_index
        self.player_sprite = arcade.Sprite()
        self.player_sprite.texture = arcade.load_texture("sprites/sprite_sheet.png", x = 0, y = 32*self.char_index, width = 32, height = 32)
        self.player_sprite.scale = 3
        self.player_sprite.center_x = pos_x
        self.player_sprite.center_y = pos_y

        self.top_speed = car_stats[0]
        self.acceleration = car_stats[1]
        self.break_speed = car_stats[2]
        self.handling = car_stats[3]

        self.speed = 0
        self.direction = 0
        self.drift_offset = 30

        self.name = name

        self.pressed_keys = []
        
        # mouse pos
        self.mouse_x = 0
        self.mouse_y = 0
        
        # movement keys
        self.forward_key = arcade.key.W
        self.break_key = arcade.key.S
        self.left_key = arcade.key.A
        self.right_key = arcade.key.D
        self.drift_key = keybinds[0]
    

    def key_pressed(self, key, modifiers):
        if key not in self.pressed_keys:
            self.pressed_keys.append(key)

        if key == self.drift_key:
            self.top_speed *= 0.8
            self.speed *= 0.8
            self.acceleration *= 0.8
            self.handling /= 0.8
            
            if self.left_key in self.pressed_keys and self.right_key not in self.pressed_keys:
                self.player_sprite.angle += self.drift_offset
            
            elif self.left_key not in self.pressed_keys and self.right_key in self.pressed_keys:
                self.player_sprite.angle -= self.drift_offset
    

    def key_released(self, key, modifiers):
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
        
        if key == self.drift_key:
            self.top_speed /= 0.8
            self.acceleration /= 0.8
            self.handling *= 0.8
            
            self.direction = self.player_sprite.angle

    def update(self, delta_time):

        if self.forward_key in self.pressed_keys:
            self.speed += self.acceleration * delta_time * 60
            if self.speed > self.top_speed:
                self.speed = self.top_speed
        
        if self.break_key in self.pressed_keys:
            self.speed -= self.break_speed * delta_time * 60
            if self.speed < 0:
                self.speed = 0

        if self.speed > 0:
            if self.right_key in self.pressed_keys:
                self.direction -= self.handling * delta_time * 60
                self.player_sprite.angle -= self.handling * delta_time * 60
            
            if self.left_key in self.pressed_keys:
                self.direction += self.handling * delta_time * 60
                self.player_sprite.angle += self.handling * delta_time * 60

        
        # movement calculations

        self.player_sprite.change_y = math.cos(math.radians(-self.direction)) * self.speed
        self.player_sprite.change_x = math.sin(math.radians(-self.direction)) * self.speed

        if self.speed > 0:
            self.speed -= 0.05 * delta_time * 30
            
        
        
        
    def draw(self):
        self.player_sprite.draw(pixelated=True)

        arcade.draw_text(self.name, self.player_sprite.center_x, self.player_sprite.center_y+40, arcade.color.WHITE, 12, anchor_x="center", font_name="Kenney Mini Square")
        
    
class OtherPlayer():
    def __init__(self, pos_x, pos_y, char_index, name):
        
        # player variables
        self.char_index = char_index
        self.player_sprite = arcade.Sprite()
        self.player_sprite.texture = arcade.load_texture("sprites/sprite_sheet.png", x = 0, y = 32*self.char_index, width = 32, height = 32)
        self.player_sprite.scale = 3
        self.player_sprite.center_x = pos_x
        self.player_sprite.center_y = pos_y

        self.name = name
        
    def draw(self):
        self.player_sprite.draw(pixelated=True)

        arcade.draw_text(self.name, self.player_sprite.center_x, self.player_sprite.center_y+40, arcade.color.WHITE, 12, anchor_x="center", font_name="Kenney Mini Square")


class MainMenu(arcade.View):
    """ Menu class to host and connect """
    def __init__(self):
        super().__init__()

        self.init_data = ""
        
        # init gui manager
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        
        # Create a vertical BoxGroup to align buttons
        self.v_box = arcade.gui.UIBoxLayout()

        # Create the buttons
        host_button = arcade.gui.UIFlatButton(text="Host", width=200, style=self.window.button_style)
        self.v_box.add(host_button.with_space_around(bottom=20))
        
        join_button = arcade.gui.UIFlatButton(text="Join", width=200, style=self.window.button_style)
        self.v_box.add(join_button.with_space_around(bottom=20))

        swap_button = arcade.gui.UIFlatButton(text="Edit Profile", width=200, style=self.window.button_style)
        self.v_box.add(swap_button.with_space_around(bottom=20))    
        
        
        @host_button.event("on_click")
        def on_click_settings(event):
            self.manager.disable()
            self.init_data = edit_file.get_name() + str(edit_file.get_character_id())
            self.window.server_thread = threading.Thread(target=server.main)
            self.window.server_thread.start()
            self.window.n = Network(self.window.server, self.init_data)
            self.window.lobby = LobbyHost()
            self.window.show_view(self.window.lobby)
            
        @join_button.event("on_click")
        def on_click_settings(event):
            self.manager.disable()
            self.window.getaddress = GetAddress()
            self.window.show_view(self.window.getaddress)

        @swap_button.event("on_click")
        def on_click_settings(event):
            self.manager.disable()
            self.window.swapdata = SwapData()
            self.window.show_view(self.window.swapdata)     
        
        # Create a widget to hold the v_box widget, that will center the buttons
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                align_y = -SCREEN_HEIGHT/6,
                child=self.v_box)
            )
            
            
    def on_draw(self):
        arcade.start_render()
        self.manager.draw()


class LobbyHost(arcade.View):
    """ lobby menu for the host """
    def __init__(self):
        super().__init__()

        self.all_init_data = ""

        self.started = False

        # init gui manager
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        
        # Create a vertical BoxGroup to align buttons
        self.v_box = arcade.gui.UIBoxLayout()

        # Create the buttons
        start_button = arcade.gui.UIFlatButton(text="Start", width=200, style=self.window.button_style)
        self.v_box.add(start_button.with_space_around(bottom=20))
        
        
        @start_button.event("on_click")
        def on_click_settings(event):
            self.manager.disable()
            self.started = True
        
        # Create a widget to hold the v_box widget, that will center the buttons
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                align_y = -SCREEN_HEIGHT/6,
                child=self.v_box)
            )
            
            
    def on_draw(self):
        arcade.start_render()

        self.all_init_data = self.window.n.recv()
        if self.all_init_data[-5:] == "start":
            self.window.game = Game(self.all_init_data[:-5])
            self.window.show_view(self.window.game)

        if self.started == True:
            self.window.n.send("start")
            self.started = None
        if self.started == False:
            self.window.n.send(" ")
        
        self.manager.draw()
           

        arcade.draw_text("Your IPv4: " + self.window.n.server, SCREEN_WIDTH/2, 7 * SCREEN_HEIGHT/8, arcade.color.WHITE, 20, anchor_x="center", font_name="Kenney Mini Square")
        arcade.draw_text("Players: " + self.all_init_data, SCREEN_WIDTH/2, 6 * SCREEN_HEIGHT/8, arcade.color.WHITE, 20, anchor_x="center", font_name="Kenney Mini Square")

        


class LobbyGuest(arcade.View):
    """ lobby menu for the host """
    def __init__(self):
        super().__init__()

        self.all_init_data = ""
        self.started = False
            
            
    def on_draw(self):
        arcade.start_render()

        self.all_init_data = self.window.n.recv()
        if self.all_init_data[-5:] == "start":
            self.started = True
            self.window.game = Game(self.all_init_data[:-5])
            self.window.show_view(self.window.game)
        if self.started == False:
            self.window.n.send(" ")


        arcade.draw_text("Players: " + self.all_init_data, SCREEN_WIDTH/2, 6 * SCREEN_HEIGHT/8, arcade.color.WHITE, 20, anchor_x="center", font_name="Kenney Mini Square")


class GetAddress(arcade.View):
    """ get address for joining player """
    def __init__(self):
        super().__init__()

        self.init_data = edit_file.get_name() + str(edit_file.get_character_id())
        
        self.viable_keys = (arcade.key.KEY_0, arcade.key.KEY_1,
                            arcade.key.KEY_2, arcade.key.KEY_3,
                            arcade.key.KEY_4, arcade.key.KEY_5,
                            arcade.key.KEY_6, arcade.key.KEY_7,
                            arcade.key.KEY_8, arcade.key.KEY_9,
                            arcade.key.PERIOD)
        
        self.server = ""
        
    
    def on_key_press(self, key, modifiers):
        if key in self.viable_keys:
            self.server += chr(key)
        elif key == arcade.key.BACKSPACE:
            self.server = self.server[:-1]
        elif key == arcade.key.ENTER:
            try:
                self.window.n = Network(self.server, self.init_data)
                self.window.lobby = LobbyGuest()
                self.window.show_view(self.window.lobby)
            except:
                self.server = "invalid ip"
    
    def on_draw(self):
        arcade.start_render()
        arcade.draw_text("Host IPv4: " + self.server, SCREEN_WIDTH/2, SCREEN_HEIGHT/2, arcade.color.WHITE, 20, anchor_x="center", font_name="Kenney Mini Square")


class SwapData(arcade.View):
    """ swap player data like name and character id """
    def __init__(self):
        super().__init__()

        self.editing_name = True # editing name = False means editing character id

        self.name = edit_file.get_name()

        self.character_id = edit_file.get_character_id()

        self.viable_keys = (arcade.key.KEY_0, arcade.key.KEY_1, arcade.key.KEY_2)

        # init gui manager
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        
        # Create a vertical BoxGroup to align buttons
        self.v_box = arcade.gui.UIBoxLayout()

        # Create the buttons
        back_button = arcade.gui.UIFlatButton(text="Back to Menu", width=200, style=self.window.button_style)
        self.v_box.add(back_button.with_space_around(bottom=20))

        @back_button.event("on_click")
        def on_click_settings(event):
            self.manager.disable()
            edit_file.swap_character_id(self.character_id)
            edit_file.swap_name(self.name)
            self.window.mainmenu = MainMenu()
            self.window.show_view(self.window.mainmenu)

        # Create a widget to hold the v_box widget, that will center the buttons
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                align_y = -SCREEN_HEIGHT/6,
                child=self.v_box)
            )

    def on_key_press(self, key, modifiers):

        if key == arcade.key.DOWN:
            self.editing_name = False

        elif key == arcade.key.UP:
            self.editing_name = True


        elif self.editing_name == True:
            if key == arcade.key.BACKSPACE:
                self.name = self.name[:-1]
            elif key == arcade.key.SPACE:
                self.name += "_"
            else:
                if len(self.name) < 20:
                    char = chr(key)
                    if char.isalnum():
                        self.name += char

        elif self.editing_name == False:
            if key in self.viable_keys:
                self.character_id = int(chr(key))
                
    def on_draw(self):
        arcade.start_render()
        self.manager.draw()

        arcade.draw_text("Your  Name: " + self.name, SCREEN_WIDTH/2,
                        6 * SCREEN_HEIGHT/8, arcade.color.WHITE, 20, 
                        anchor_x="center", font_name="Kenney Mini Square", bold=self.editing_name)

        arcade.draw_text("Your Character ID: " + str(self.character_id), SCREEN_WIDTH/2,
                        5 * SCREEN_HEIGHT/8, arcade.color.WHITE, 20, 
                        anchor_x="center", font_name="Kenney Mini Square", bold=not self.editing_name)
        

        arcade.draw_text("Arrow Keys to Swap", SCREEN_WIDTH/2,
                        4 * SCREEN_HEIGHT/8, arcade.color.WHITE, 20, 
                        anchor_x="center", font_name="Kenney Mini Square")


class GameWindow(arcade.Window):
    """ Main Window """
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.set_location(0,0)
        self.set_fullscreen(False)

        arcade.set_background_color(arcade.color.BLACK)
        
        self.button_style = {"font_name" : "Kenney Pixel", "font_size" : 30}
        
        self.done = False
        
    def on_close(self):
        self.done = True
        self.close()
    
        
        
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



def main():
    window = GameWindow()
    window.mainmenu = MainMenu()
    window.show_view(window.mainmenu)
    window.server = get_local_ipv4()
    arcade.run()
    

if __name__ == "__main__":
    main()