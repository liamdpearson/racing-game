# Liam Pearson
# Oct 7 2025
# Multiplayer Game Client


import arcade # type: ignore
import arcade.gui # type: ignore
import threading
import socket

from network import Network
import server
import edit_file
import objects



SCREEN_WIDTH, SCREEN_HEIGHT = arcade.window_commands.get_display_size()

#SCREEN_WIDTH, SCREEN_HEIGHT = 500, 500


class Game(arcade.View):
    """ Actual Game Function """
    def __init__(self, all_init_data):
        super().__init__()

        print(all_init_data)

        self.fps = 0

        self.start_pos = read_pos(self.window.n.getData())
        
        self.player = None
        self.other_players = []

        self.all_init_data = all_init_data.split()
        self.player_index = int(self.all_init_data[0])
        self.players = self.all_init_data[1:]
        self.player_data = self.players[self.player_index]
        self.other_players_data = self.players[:self.player_index] + self.players[self.player_index+1:]

        self.char_index = int(self.player_data[-1])
        self.name = self.player_data[:-1]
        
        self.all_positions = None
        
        self.listen_thread = threading.Thread(target=self.listen_for_updates, daemon = True)
        self.listen_thread.start()

        #top speed, acceleration, break_speed, handling. perfect stats: 20, 0.25, 0.3, 2.5
        self.car_stats = ((20, 0.15, 0.2, 2), (18, 0.25, 0.25, 2.25), (19, 0.2, 0.225, 2.125))
        
        self.tile_map = None
        self.wall_list = None
        
        self.camera = None
        self.gui_camera = None
        
        self.physics_engine = None

        self.start_counter = 10
        self.locked = True
        self.current_place = 0
        self.laps_to_go_msg = "3 laps to go"
        
        self.setup()
    
    
    
    def setup(self):
        
        # setup map and walls
        self.tile_map = arcade.load_tilemap("maps/map1.json", scaling=3, offset=(0,0))
        self.tire_list = self.tile_map.sprite_lists["AllWalls"]
        self.light_list = self.tile_map.sprite_lists["Lights"]
        self.wall_list = self.tile_map.sprite_lists["Walls"]
        self.floor_list = self.tile_map.sprite_lists["Floor"]
        self.finishline = self.tile_map.sprite_lists["FinishLine"]
        self.speedboosts = self.tile_map.sprite_lists["SpeedBoosts"]
        self.dirtpatches = self.tile_map.sprite_lists["SlowSpots"]
        
        # pos x, pos y, move speed, anim speed, char index, 
        self.player = objects.Player(self.start_pos[0], self.start_pos[1], self.car_stats[self.char_index], [arcade.key.LSHIFT], self.char_index, self.name)

        for player in self.other_players_data:
            self.other_players.append(objects.OtherPlayer(0, 0, int(player[-1]), player[:-1]))
        
        # setup cameras
        self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.gui_camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # setup physics engine
        self.physics_engine = arcade.PhysicsEngineSimple(self.player.player_sprite, self.wall_list)
        
        # camera offset
        self.cam_offset_x = SCREEN_WIDTH/2
        self.cam_offset_y = SCREEN_HEIGHT/2

        
    
    
    def listen_for_updates(self):
        while self.window.done == False:
            if not self.window.n.update():
                self.window.n = None
                self.window.mainmenu = MainMenu()
                self.window.show_view(self.window.mainmenu)
                self.window.done = True
            
        print("listening stopped")
        return None
        
    
        
    def on_draw(self):
        arcade.start_render()
        
        self.camera.use()
        
        self.floor_list.draw(pixelated = True)
        self.dirtpatches.draw(pixelated = True)
        self.tire_list.draw(pixelated = True)
        self.light_list.draw(pixelated = True)
        self.finishline.draw(pixelated = True)
        self.speedboosts.draw(pixelated = True)
        
        
        
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
        

        #draw fps
        arcade.draw_text(str(self.fps) + " fps", 15, SCREEN_HEIGHT-35, arcade.color.WHITE, 20, font_name="Kenney Mini Square")
        arcade.draw_text(str(self.current_place), SCREEN_HEIGHT/10 + 5, SCREEN_HEIGHT/10 - 5, arcade.color.EERIE_BLACK, SCREEN_HEIGHT/10, font_name="Kenney Blocks")
        arcade.draw_text(str(self.current_place), SCREEN_HEIGHT/10, SCREEN_HEIGHT/10, self.window.place_colors[self.current_place], SCREEN_HEIGHT/10, font_name="Kenney Blocks")
        arcade.draw_text(self.laps_to_go_msg, SCREEN_WIDTH/2, 24*SCREEN_HEIGHT/25, arcade.color.WHITE, SCREEN_HEIGHT/30, anchor_x="center", font_name="Kenney Mini Square")
        #arcade.draw_text(str(self.player.marker.int_for_sorting), SCREEN_WIDTH/2, 9*SCREEN_HEIGHT/10, arcade.color.YELLOW, SCREEN_HEIGHT/20, anchor_x="center", font_name="Kenney Mini Square")

        
        
    def on_update(self, delta_time):

        #update fps
        self.fps = int(1/delta_time)

        multiplier = 60*delta_time
            
        self.physics_engine.update()
        if self.locked:
            self.start_counter -= delta_time
            if self.start_counter < 0:
                self.locked = False
        else:
            self.player.update(multiplier)
        
        cam_pos_x = self.player.player_sprite.center_x - self.cam_offset_x
        cam_pos_y = self.player.player_sprite.center_y - self.cam_offset_y
        
        self.camera.move_to((cam_pos_x, cam_pos_y))
        
        if self.window.n:
            self.window.n.p_data = make_pos((self.player.player_sprite.center_x,
                                            self.player.player_sprite.center_y,
                                            self.player.player_sprite.angle,
                                            self.player.marker.int_for_sorting
                                            ))
        
        
        if self.window.n.all_data:
            if self.window.n.all_data[-1] == "f":
                finished_players = self.window.n.all_data.split()[-1][:-1]
                self.window.done = True
                self.window.n = None
                self.endscreen = EndScreen(finished_players, self.players)
                self.window.show_view(self.endscreen)
            else:
                self.current_place = int(self.window.n.all_data[-1])
                self.all_positions = self.window.n.all_data[:-1].split()
                del self.all_positions[self.player_index]
                if self.all_positions:
                    for i in range(len(self.all_positions)):
                            data = read_pos(self.all_positions[i])
                            if len(data) == 3:
                                player = self.other_players[i]
                                player.player_sprite.center_x = data[0]
                                player.player_sprite.center_y = data[1]
                                player.player_sprite.angle = data[2]

        # finish line check
        if arcade.check_for_collision_with_list(self.player.player_sprite, self.finishline):
            if self.player.marker.total_checkpoints == 28:
                self.laps_to_go_msg = "2 laps to go"
            elif self.player.marker.total_checkpoints == 56:
                self.laps_to_go_msg = "Final lap!"
            elif self.player.marker.total_checkpoints == 84:
                self.player.marker.total_checkpoints += 1
        
        # speedboost check
        if arcade.check_for_collision_with_list(self.player.player_sprite, self.speedboosts):
            self.player.speed += 1.5 * multiplier
        
        if arcade.check_for_collision_with_list(self.player.player_sprite, self.dirtpatches):
            self.player.speed *= 0.95**multiplier
        


    def on_key_press(self, key, modifiers):
        self.player.key_pressed(key, modifiers)
    

    def on_key_release(self, key, modifiers):
        self.player.key_released(key, modifiers)
            
        
    #def on_mouse_motion(self, x, y, dx, dy):
        #self.player.mouse_x, self.player.mouse_y = x-SCREEN_WIDTH/2, y-SCREEN_HEIGHT/2


class EndScreen(arcade.View):
    """ Menu class to host and connect """
    def __init__(self, order, players):
        super().__init__()
    
        self.order = order
        self.players = players
        
        # init gui manager
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        
        # Create a vertical BoxGroup to align buttons
        self.v_box = arcade.gui.UIBoxLayout()

        # Create the buttons
        mainmenu_button = arcade.gui.UIFlatButton(text="Main Menu", width=200, style=self.window.button_style)
        self.v_box.add(mainmenu_button.with_space_around(bottom=20))
        
            
        @mainmenu_button.event("on_click")
        def on_click_settings(event):
            self.manager.disable()
            self.window.done = False
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
            
            
    def on_draw(self):
        arcade.start_render()
        self.manager.draw()

        for i in range(len(self.order)):
            arcade.draw_text(str(i+1) + ". " + self.players[int(self.order[i])][:-1], SCREEN_WIDTH/2, 3 * SCREEN_HEIGHT/4 - 50*i, self.window.place_colors[i+1], 40, anchor_x="center", font_name="Kenney Mini Square")


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

        quit_button = arcade.gui.UIFlatButton(text="Quit Game", width=200, style=self.window.button_style)
        self.v_box.add(quit_button.with_space_around(bottom=20))
        
        
        @host_button.event("on_click")
        def on_click_settings(event):
            self.manager.disable()
            self.init_data = edit_file.get_name() + str(edit_file.get_character_id())
            self.window.server_thread = threading.Thread(target=server.main, daemon = True)
            self.window.server_thread.start()
            self.window.n = Network(self.init_data)
            self.window.n.set_server(self.window.server)
            self.window.n.connect()
            self.window.hosting = True
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

        @quit_button.event("on_click")
        def on_click_settings(event):
            self.manager.disable()
            self.window.done = True
            self.window.close()  
        
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

        arcade.draw_text("Version Alpha 1.1", SCREEN_WIDTH/50, SCREEN_HEIGHT/25, arcade.color.WHITE, SCREEN_WIDTH/100, font_name="Kenney Mini Square")
        arcade.draw_text("Racing Game", SCREEN_WIDTH/2, 3*SCREEN_HEIGHT/4, arcade.color.WHITE, SCREEN_WIDTH/20, anchor_x="center", font_name="Kenney Mini Square")


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

        back_button = arcade.gui.UIFlatButton(text="Back to Menu", width=200, style=self.window.button_style)
        self.v_box.add(back_button.with_space_around(bottom=20))

        @back_button.event("on_click")
        def on_click_settings(event):
            self.manager.disable()
            self.window.n = None
            self.window.mainmenu = MainMenu()
            self.window.show_view(self.window.mainmenu)
        
        @start_button.event("on_click")
        def on_click_settings(event):
            self.manager.disable()
            self.started = True
        
        # Create a widget to hold the v_box widget, that will center the buttons
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                align_y = -SCREEN_HEIGHT/3,
                child=self.v_box)
            )
            
            
    def on_draw(self):
        arcade.start_render()

        if self.started == True:
            self.window.n.send("start")
            self.started = None
        if self.started == False:
            self.window.n.send(" ")

        self.all_init_data = self.window.n.recv()
        lis = self.all_init_data.split("|")
        self.window.n.p_data = lis[0]
        self.all_init_data = lis[1]

        if self.all_init_data[-5:] == "start":
            self.window.game = Game(self.all_init_data[:-5])
            self.window.show_view(self.window.game)
        
        self.manager.draw()

        data = self.all_init_data.split()
        p_list = data[1:]
        player_index = int(data[0])

        arcade.draw_text("You are player " + str(player_index+1), SCREEN_WIDTH/2, 6.5 * SCREEN_HEIGHT/8, arcade.color.WHITE, 20, anchor_x="center", font_name="Kenney Mini Square")

        for i in range(len(p_list)):
            arcade.draw_text("Player " + str(i+1) + ": " + p_list[i][:-1], SCREEN_WIDTH/2, 6 * SCREEN_HEIGHT/8-i*30, arcade.color.WHITE, 20, anchor_x="center", font_name="Kenney Mini Square")

        arcade.draw_text("Your IPv4: " + self.window.n.server, SCREEN_WIDTH/2, 7 * SCREEN_HEIGHT/8, arcade.color.WHITE, 20, anchor_x="center", font_name="Kenney Mini Square")
        


class LobbyGuest(arcade.View):
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
        back_button = arcade.gui.UIFlatButton(text="Back to Menu", width=200, style=self.window.button_style)
        self.v_box.add(back_button.with_space_around(bottom=20))

        @back_button.event("on_click")
        def on_click_settings(event):
            self.manager.disable()
            self.window.n = None
            self.window.mainmenu = MainMenu()
            self.window.show_view(self.window.mainmenu)

        # Create a widget to hold the v_box widget, that will center the buttons
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                align_y = -SCREEN_HEIGHT/3,
                child=self.v_box)
            )
            
            
    def on_draw(self):
        arcade.start_render()
        self.manager.draw()
        
        if self.started == False:
            self.window.n.send(" ")
            try:
                self.all_init_data = self.window.n.recv()
            except:
                self.window.n = None
                self.window.mainmenu = MainMenu()
                self.window.show_view(self.window.mainmenu)
                return

        lis = self.all_init_data.split("|")
        self.window.n.p_data = lis[0]
        self.all_init_data = lis[1]

        if self.all_init_data[-5:] == "start":
            self.started = True
            self.window.game = Game(self.all_init_data[:-5])
            self.window.show_view(self.window.game)

        data = self.all_init_data.split()
        p_list = data[1:]
        player_index = int(data[0])

        arcade.draw_text("You are player " + str(player_index+1), SCREEN_WIDTH/2, 6.5 * SCREEN_HEIGHT/8, arcade.color.WHITE, 20, anchor_x="center", font_name="Kenney Mini Square")
        for i in range(len(p_list)):
            arcade.draw_text("Player " + str(i+1) + ": " + p_list[i][:-1], SCREEN_WIDTH/2, 6 * SCREEN_HEIGHT/8-i*30, arcade.color.WHITE, 20, anchor_x="center", font_name="Kenney Mini Square")


class GetAddress(arcade.View):
    """ get address for joining player """
    def __init__(self):
        super().__init__()

        self.init_data = edit_file.get_name() + str(edit_file.get_character_id())
        self.window.n = Network(self.init_data)
        
        self.viable_keys = (arcade.key.KEY_0, arcade.key.KEY_1,
                            arcade.key.KEY_2, arcade.key.KEY_3,
                            arcade.key.KEY_4, arcade.key.KEY_5,
                            arcade.key.KEY_6, arcade.key.KEY_7,
                            arcade.key.KEY_8, arcade.key.KEY_9,
                            arcade.key.PERIOD)
        
        self.server = ""


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
            self.window.mainmenu = MainMenu()
            self.window.show_view(self.window.mainmenu)

        # Create a widget to hold the v_box widget, that will center the buttons
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                align_y = -SCREEN_HEIGHT/3,
                child=self.v_box)
            )
        
    
    def on_key_press(self, key, modifiers):
        if key in self.viable_keys:
            self.server += chr(key)
        elif key == arcade.key.BACKSPACE:
            self.server = self.server[:-1]
        elif key == arcade.key.ENTER:
            self.window.n.set_server(self.server)
            a = self.window.n.connect()
            if a:               
                self.window.lobby = LobbyGuest()
                self.window.show_view(self.window.lobby)
            else:
                self.server = "invalid ip"
    
    def on_draw(self):
        arcade.start_render()
        self.manager.draw()
        
        arcade.draw_text("Host IPv4: " + self.server, SCREEN_WIDTH/2, SCREEN_HEIGHT/2, arcade.color.WHITE, 20, anchor_x="center", font_name="Kenney Mini Square")


class SwapData(arcade.View):
    """ swap player data like name and character id """
    def __init__(self):
        super().__init__()

        self.name = edit_file.get_name()

        self.character_id = edit_file.get_character_id()

        self.car_sprites = []
        for i in range(3):
            sprite = arcade.Sprite(scale = 5)
            sprite.center_x = SCREEN_WIDTH/2 + (i-1)*200
            sprite.center_y = 5*SCREEN_HEIGHT/8
            tex = arcade.load_texture("sprites/sprite_sheet.png", x = 32*i, y = 0, width = 32, height = 71)
            sprite.texture = tex

            self.car_sprites.append(sprite)
        
        self.rect_x = self.car_sprites[self.character_id].center_x
        self.rect_y = 5*SCREEN_HEIGHT/8

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
                align_y = -SCREEN_HEIGHT/3,
                child=self.v_box)
            )

    def on_key_press(self, key, modifiers):

        if key == arcade.key.BACKSPACE:
            self.name = self.name[:-1]
        if len(self.name) < 20:
            if key == arcade.key.SPACE:
                self.name += "_"
            else:
                char = chr(key)
                if char.isalnum():
                    self.name += char
    
    def on_mouse_press(self, x, y, button, modifiers):
        for i in range(3):
            if self.car_sprites[i].collides_with_point((x,y)):
                self.character_id = i
                edit_file.swap_character_id(i)
                self.rect_x = self.car_sprites[i].center_x
                
    def on_draw(self):
        arcade.start_render()
        self.manager.draw()

        arcade.draw_text("Your  Name: " + self.name, SCREEN_WIDTH/2,
                        7 * SCREEN_HEIGHT/8, arcade.color.WHITE, 20, 
                        anchor_x="center", font_name="Kenney Mini Square")
        
        arcade.draw_rectangle_outline(self.rect_x, self.rect_y, 200,375, arcade.color.WHITE)
        
        for car in self.car_sprites:
            car.draw(pixelated=True)


class GameWindow(arcade.Window):
    """ Main Window """
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.set_location(0,0)
        self.set_fullscreen(False)

        arcade.set_background_color(arcade.color.BLACK)
        
        self.button_style = {"font_name" : "Kenney Pixel", "font_size" : 30}
        
        self.done = False

        self.place_colors = {1 : arcade.color.GOLD,
                             2 : arcade.color.SILVER,
                               3: arcade.color.BRONZE,
                                 4: arcade.color.GRAY,
                                   5: arcade.color.GRAY}
        
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