# Liam Pearson
# Multiplayer Racing Game Client


import arcade # type: ignore
import arcade.gui # type: ignore
import threading
import socket

from data.scripts.network import Network
import data.scripts.server as server
import data.scripts.edit_file as edit_file
import data.scripts.objects as objects
from data.scripts.constants import MAP_SCALE_MULTIPLIER, SCREEN_WIDTH, SCREEN_HEIGHT, SCALE_MULTIPLIER, DIST_FROM_CORNER, SPEED_BOOST_SOUND


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
        self.map_index = int(self.players[0][-1])
        self.players[0] = self.players[0][:-1]
        self.player_data = self.players[self.player_index]
        self.other_players_data = self.players[:self.player_index] + self.players[self.player_index+1:]

        self.char_index = int(self.player_data[-1])
        self.name = self.player_data[:-1]
        
        self.all_positions = None
        
        self.listen_thread = threading.Thread(target=self.listen_for_updates, daemon = True)

        #top speed, acceleration, break_speed, handling. perfect stats: 25, 0.25, 0.3, 2.5
        self.car_stats = ((25, 0.18, 0.2, 2), (22.5, 0.3, 0.25, 2.25), (23.75, 0.24, 0.225, 2.125))
        
        self.tile_map = None
        self.wall_list = None
        
        self.camera = None
        self.gui_camera = None
        
        self.physics_engine = None

        self.start_counter = 8
        self.locked = True
        self.current_place = 1
        self.laps_left = 3

        self.col_w_speedboost = False
        self.should_go_back_to_menu = False
        
        self.setup()
    
    
    
    def setup(self):
        
        # setup map and walls
        self.tile_map = arcade.load_tilemap("data/maps/map" + str(self.map_index + 1) + ".json", scaling=3*MAP_SCALE_MULTIPLIER, offset=(0,0))
        self.tire_list = self.tile_map.sprite_lists["AllWalls"]
        self.decor_list = self.tile_map.sprite_lists["Decor"]
        self.wall_list = self.tile_map.sprite_lists["Walls"]
        self.floor_list = self.tile_map.sprite_lists["Floor"]
        self.finishline = self.tile_map.sprite_lists["FinishLine"]
        self.speedboosts = self.tile_map.sprite_lists["SpeedBoosts"]
        self.dirtpatches = self.tile_map.sprite_lists["SlowSpots"]
        self.background = self.tile_map.sprite_lists["Background"]
        
        # pos x, pos y, move speed, anim speed, char index, 
        self.player = objects.Player(self.start_pos[0], self.start_pos[1], self.car_stats[self.char_index], [arcade.key.LSHIFT], self.char_index, self.name, self.map_index)
        for player in self.other_players_data:
            op = objects.OtherPlayer(int(player[-1]), player[:-1])
            self.other_players.append(op)
            self.wall_list.append(op.player_sprite)
            print("op created")
        
        self.listen_thread.start()

        
        # setup cameras
        self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.gui_camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # setup physics engine
        self.physics_engine = arcade.PhysicsEngineSimple(self.player.player_sprite, self.wall_list)
        
        # camera offset
        self.cam_offset_x = SCREEN_WIDTH/2
        self.cam_offset_y = SCREEN_HEIGHT/2

        
    
    
    def listen_for_updates(self):
        while not self.window.done and self.window.n:
            if not self.window.n.update():
                self.should_go_back_to_menu = True

            self.update_other_players()
            
        print("listening stopped")
        return None



    def update_other_players(self):
        data = self.window.n.all_data
        if data:
            if data[-1] == "f":
                finished_players = data.split()[-1][:-1]
                self.window.done = True
                self.window.n = None
                self.window.endscreen = EndScreen(finished_players, self.players)
                self.window.show_view(self.window.endscreen)
            else:
                self.current_place = int(data[-1])
                self.all_positions = data[:-1].split()
                del self.all_positions[self.player_index]
                if self.all_positions:
                    for i in range(len(self.all_positions)):
                            p_data = read_pos(self.all_positions[i])
                            if len(p_data) == 5:
                                self.other_players[i].accept_data(
                                    p_data[0] * MAP_SCALE_MULTIPLIER, # x
                                    p_data[1] * MAP_SCALE_MULTIPLIER, # y
                                    p_data[2], # angle
                                    p_data[3], # speed
                                    p_data[4]  # boosting
                                )
        
    
        
    def on_draw(self):
        arcade.start_render()
        
        self.camera.use()
        
        self.background.draw(pixelated = True)
        self.floor_list.draw(pixelated = True)
        self.finishline.draw(pixelated = True)
        self.dirtpatches.draw(pixelated = True)
        self.tire_list.draw(pixelated = True)
        self.decor_list.draw(pixelated = True)
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
        arcade.draw_text(str(self.fps) + " fps", 15, 44*SCREEN_HEIGHT/45, arcade.color.WHITE, 20*SCALE_MULTIPLIER, font_name="Kenney Mini Square")
        arcade.draw_text(str(self.current_place), SCREEN_HEIGHT/10 + 5, SCREEN_HEIGHT/10 - 5, arcade.color.EERIE_BLACK, 150 * SCALE_MULTIPLIER, font_name="Kenney Blocks")
        arcade.draw_text(str(self.current_place), SCREEN_HEIGHT/10, SCREEN_HEIGHT/10, self.window.place_colors[self.current_place], 150 * SCALE_MULTIPLIER, font_name="Kenney Blocks")
        if self.laps_left > 0:
            arcade.draw_text("Lap " + str(4 - self.laps_left) + "/3", SCREEN_WIDTH/2, 24*SCREEN_HEIGHT/25, arcade.color.WHITE, 50 * SCALE_MULTIPLIER, anchor_x="center", font_name="Kenney Mini Square")
        #arcade.draw_text(str(self.player.marker.int_for_sorting), SCREEN_WIDTH/2, 9*SCREEN_HEIGHT/10, arcade.color.YELLOW, SCREEN_HEIGHT/20, anchor_x="center", font_name="Kenney Mini Square")

        
        
    def on_update(self, delta_time):

        #check if should go back to menu
        if self.should_go_back_to_menu:
            self.window.n = None
            self.window.mainmenu = MainMenu()
            self.window.show_view(self.window.mainmenu)
            return

        #update fps
        if delta_time > 0:
            self.fps = int(1 / delta_time)

        multiplier = 60*delta_time
            
        self.physics_engine.update()
        if self.locked:
            self.start_counter -= delta_time
            if self.start_counter < 0:
                self.locked = False
        else:
            self.player.update(multiplier)
        
        for p in self.other_players:
            p.update(multiplier)
        
        cam_pos_x = self.player.player_sprite.center_x - self.cam_offset_x
        cam_pos_y = self.player.player_sprite.center_y - self.cam_offset_y
        
        self.camera.move_to((cam_pos_x, cam_pos_y))
        
        if self.window.n:
            self.window.n.p_data = make_pos((self.player.player_sprite.center_x / MAP_SCALE_MULTIPLIER,
                                            self.player.player_sprite.center_y / MAP_SCALE_MULTIPLIER,
                                            self.player.player_sprite.angle,
                                            self.player.speed,
                                            self.player.draw_boost,
                                            self.player.marker.int_for_sorting
                                            ))
            
        # finish line check
        if arcade.check_for_collision_with_list(self.player.player_sprite, self.finishline):
            if self.player.marker.total_checkpoints == self.player.marker.checkpoints_per_lap:
                self.laps_left = 2
            elif self.player.marker.total_checkpoints == self.player.marker.checkpoints_per_lap * 2:
                self.laps_left = 1
            elif self.player.marker.total_checkpoints == self.player.marker.checkpoints_per_lap * 3:
                self.laps_left = 0
                self.player.marker.total_checkpoints += 1
        
        # speedboost check
        if arcade.check_for_collision_with_list(self.player.player_sprite, self.speedboosts):
            self.player.speed += 1.15 * multiplier
            if not self.col_w_speedboost:
                self.col_w_speedboost = True
                SPEED_BOOST_SOUND.force_play_sound(0.1)
        else:
            self.col_w_speedboost = False
        
        if arcade.check_for_collision_with_list(self.player.player_sprite, self.dirtpatches):
            self.player.speed *= 0.96**multiplier
        


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
            self.window.endscreen = None
            
        
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
            self.window.choose_map = ChooseMap()
            self.window.show_view(self.window.choose_map)
            self.window.mainmenu = None
            
        @join_button.event("on_click")
        def on_click_settings(event):
            self.manager.disable()
            self.window.getaddress = GetAddress()
            self.window.show_view(self.window.getaddress)
            self.window.mainmenu = None

        @swap_button.event("on_click")
        def on_click_settings(event):
            self.manager.disable()
            self.window.swapdata = SwapData()
            self.window.show_view(self.window.swapdata)
            self.window.mainmenu = None

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

        arcade.draw_text("Version Alpha 1.2", SCREEN_WIDTH/50, SCREEN_HEIGHT/25, arcade.color.WHITE, 30 * SCALE_MULTIPLIER, font_name="Kenney Mini Square")
        arcade.draw_text("Racing Game", SCREEN_WIDTH/2, 3*SCREEN_HEIGHT/4, arcade.color.WHITE, SCREEN_WIDTH/20, anchor_x="center", font_name="Kenney Mini Square")


class ChooseMap(arcade.View):
    """ get map from host """
    def __init__(self):
        super().__init__()

        self.selected_map = 0

        self.logo_sprites = []
        for i in range(3):
            s = arcade.Sprite()
            s.texture = arcade.load_texture("data/sprites/map_logos.png", x = 0, y = 32*i, width = 128, height = 32)
            s.scale = 6*SCALE_MULTIPLIER
            s.center_x = SCREEN_WIDTH/2
            s.center_y = SCREEN_HEIGHT/2 + 192*SCALE_MULTIPLIER * (1-i)
            self.logo_sprites.append(s)

        self.rect_y = SCREEN_HEIGHT/2 + 192*SCALE_MULTIPLIER

        # init gui manager
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        
        # Create a vertical BoxGroup to align buttons
        self.v_box = arcade.gui.UIBoxLayout()

        # Create the buttons
        open_button = arcade.gui.UIFlatButton(text="Open Lobby", width=200, style=self.window.button_style)
        self.v_box.add(open_button.with_space_around(bottom=20))

        back_button = arcade.gui.UIFlatButton(text="Back to Menu", width=200, style=self.window.button_style)
        self.v_box.add(back_button.with_space_around(bottom=20))

        @open_button.event("on_click")
        def on_click_settings(event):
            self.manager.disable()
            self.init_data = edit_file.get_name() + str(edit_file.get_character_id()) 
            self.window.server_thread = threading.Thread(target=server.main, args=(self.selected_map,), daemon=True)
            self.window.server_thread.start()
            self.window.n = Network(self.init_data + str(self.selected_map))
            self.window.n.set_server(self.window.server)
            self.window.n.connect()
            self.window.hosting = True
            self.window.lobby = LobbyHost()
            self.window.show_view(self.window.lobby)
            self.window.choose_map = None
        
        @back_button.event("on_click")
        def on_click_settings(event):
            self.manager.disable()
            self.window.mainmenu = MainMenu()
            self.window.show_view(self.window.mainmenu)
            self.window.choose_map = None
        
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

        arcade.draw_text("Choose Map:", SCREEN_WIDTH/2, 7*SCREEN_HEIGHT/8, arcade.color.WHITE, 60*SCALE_MULTIPLIER, anchor_x="center", font_name="Kenney Mini Square")
        for i in self.logo_sprites:
            i.draw(pixelated=True)
        arcade.draw_rectangle_outline(SCREEN_WIDTH/2, self.rect_y, 
                                      128*6*SCALE_MULTIPLIER, 32*6*SCALE_MULTIPLIER, arcade.color.WHITE, border_width=5*SCALE_MULTIPLIER)
    
    def on_mouse_press(self, x, y, button, modifiers):
        for i in range(3):
            if self.logo_sprites[i].collides_with_point((x,y)):
                self.selected_map = i
                self.rect_y = self.logo_sprites[i].center_y

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
            self.window.lobby = None
        
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

        def back_to_menu():
            self.manager.disable()
            self.window.n = None
            self.window.mainmenu = MainMenu()
            self.window.show_view(self.window.mainmenu)
            self.window.lobby = None
        
        if self.started == True:
            self.window.n.send("start")
            self.started = None
        if self.started == False:
            self.window.n.send(" ")

        try:
            self.all_init_data = self.window.n.recv()
            if not self.all_init_data:
                back_to_menu()
                return
        except:
            back_to_menu()
            return
        
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

        arcade.draw_text("Player 1: " + p_list[0][:-2], SCREEN_WIDTH/2, 6 * SCREEN_HEIGHT/8, arcade.color.WHITE, 20, anchor_x="center", font_name="Kenney Mini Square")

        for i in range(1, len(p_list)):
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
            self.leave()

        # Create a widget to hold the v_box widget, that will center the buttons
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                align_y = -SCREEN_HEIGHT/3,
                child=self.v_box)
            )
    
    def leave(self):
        self.manager.disable()
        self.window.n = None
        self.window.mainmenu = MainMenu()
        self.window.show_view(self.window.mainmenu)
        self.window.lobby = None
            
            
    def on_draw(self):
        arcade.start_render()
        self.manager.draw()

        if self.started == False:
            self.window.n.send(" ")
            try:
                self.all_init_data = self.window.n.recv()
                if not self.all_init_data:
                    self.leave()
                    return
            except:
                self.leave()
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

        arcade.draw_text("Player 1: " + p_list[0][:-2], SCREEN_WIDTH/2, 6 * SCREEN_HEIGHT/8, arcade.color.WHITE, 20, anchor_x="center", font_name="Kenney Mini Square")

        arcade.draw_text("You are player " + str(player_index+1), SCREEN_WIDTH/2, 6.5 * SCREEN_HEIGHT/8, arcade.color.WHITE, 20, anchor_x="center", font_name="Kenney Mini Square")
        for i in range(1, len(p_list)):
            arcade.draw_text("Player " + str(i+1) + ": " + p_list[i][:-1], SCREEN_WIDTH/2, 6 * SCREEN_HEIGHT/8-i*30, arcade.color.WHITE, 20, anchor_x="center", font_name="Kenney Mini Square")


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
        self.invalid = 0

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
            self.window.n = Network(self.init_data)
            self.window.n.set_server(self.server)
            a = self.window.n.connect()
            if a:               
                self.window.lobby = LobbyGuest()
                self.window.show_view(self.window.lobby)
            else:
                self.server = ""
                self.invalid += 1
    
    def on_draw(self):
        arcade.start_render()
        self.manager.draw()
        
        arcade.draw_text("Host IPv4: " + self.server, SCREEN_WIDTH/2, SCREEN_HEIGHT/2, arcade.color.WHITE, 20, anchor_x="center", font_name="Kenney Mini Square")
        if self.invalid > 0:
            arcade.draw_text("Invalid IP Try Again", SCREEN_WIDTH/2, 3*SCREEN_HEIGHT/5, arcade.color.YELLOW, 20, anchor_x="center", font_name="Kenney Mini Square")

class SwapData(arcade.View):
    """ swap player data like name and character id """
    def __init__(self):
        super().__init__()

        self.name = edit_file.get_name()

        self.character_id = edit_file.get_character_id()

        self.car_sprites = []
        for i in range(3):
            sprite = arcade.Sprite(scale = 5*SCALE_MULTIPLIER)
            sprite.center_x = SCREEN_WIDTH/2 + (i-1)*200
            sprite.center_y = 5*SCREEN_HEIGHT/8
            tex = arcade.load_texture("data/sprites/sprite_sheet.png", x = 32*i, y = 0, width = 32, height = 71)
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
        
        arcade.draw_rectangle_outline(self.rect_x, self.rect_y,
                                      200*SCALE_MULTIPLIER,375*SCALE_MULTIPLIER, arcade.color.WHITE)
        
        for car in self.car_sprites:
            car.draw(pixelated=True)


class GameWindow(arcade.Window):
    """ Main Window """
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.set_location(DIST_FROM_CORNER,DIST_FROM_CORNER)
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
        f_tup.append(int(i))
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