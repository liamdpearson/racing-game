import data.scripts.edit_file as edit_file
import arcade
import math

from data.scripts.constants import SCALE_MULTIPLIER, MAP_SCALE_MULTIPLIER, DRIFT_BOOST_SOUND

class Marker():
    def __init__(self, player_x, player_y, map_index):
        self.total_checkpoints = 0
        self.checkpoint_index = 0

        self.int_for_sorting = 0

        self.dist_to_next_checkpoint = 1000

        # get the positions from the file and split them into a list
        self.positions = edit_file.get_positions(map_index + 1).split(",")
        self.checkpoints_per_lap = len(self.positions)
        for i in range(len(self.positions)):
            self.positions[i] = self.positions[i].split()
        
        self.x = int(self.positions[self.checkpoint_index][0]) * MAP_SCALE_MULTIPLIER
        self.y = int(self.positions[self.checkpoint_index][1]) * MAP_SCALE_MULTIPLIER

        self.dist_between_cur_and_nxt_checkpoint = math.sqrt((self.x - player_x)**2 + (self.y - player_y)**2)


        
    
    def next_position(self, player_x, player_y):

        self.total_checkpoints += 1
        self.checkpoint_index += 1

        if self.checkpoint_index >= len(self.positions):
            self.checkpoint_index = 0
        self.x = int(self.positions[self.checkpoint_index][0]) * MAP_SCALE_MULTIPLIER
        self.y = int(self.positions[self.checkpoint_index][1]) * MAP_SCALE_MULTIPLIER

        self.dist_between_cur_and_nxt_checkpoint = math.sqrt((self.x - player_x)**2 + (self.y - player_y)**2)
    
    def check_distance(self, player_x, player_y):
        self.dist_to_next_checkpoint = math.sqrt((self.x - player_x)**2 + (self.y - player_y)**2)
        if self.dist_to_next_checkpoint < 400 * MAP_SCALE_MULTIPLIER:
            self.next_position(player_x, player_y)
        
        self.int_for_sorting = int((self.total_checkpoints + 1 - self.dist_to_next_checkpoint/self.dist_between_cur_and_nxt_checkpoint)*100)
    
    #def draw(self):
    #    arcade.draw_circle_outline(self.x, self.y, 400 * MAP_SCALE_MULTIPLIER, arcade.color.YELLOW)
        
    

class Player():
    def __init__(self, pos_x, pos_y, car_stats, keybinds, char_index, name, map_index):
        super().__init__()
        
        # player variables
        self.char_index = char_index
        self.player_sprite = arcade.Sprite()
        self.player_sprite.texture = arcade.load_texture("data/sprites/sprite_sheet.png", x = 32*self.char_index, y = 0, width = 32, height = 32)
        self.player_sprite.scale = 3.5 * SCALE_MULTIPLIER
        self.player_sprite.center_x = pos_x * MAP_SCALE_MULTIPLIER
        self.player_sprite.center_y = pos_y * MAP_SCALE_MULTIPLIER

        self.boost_sprite = arcade.Sprite()
        self.boost_sprite.texture = arcade.load_texture("data/sprites/sprite_sheet.png", x = 96 + 32*self.char_index, y = 0, width = 32, height = 40)
        self.boost_sprite.scale = self.player_sprite.scale
        self.boost_sprite.center_x = self.player_sprite.center_x
        self.boost_sprite.center_y = self.player_sprite.center_y

        self.top_speed = car_stats[0]
        self.acceleration = car_stats[1]
        self.break_speed = car_stats[2]
        self.handling = car_stats[3]

        self.speed = 0
        self.direction = 0
        self.drift_offset = 30

        self.turing_left = False

        self.drifting = False
        self.drift_boost = 0
        self.boost_timer = 0
        self.draw_boost = 0

        self.name = name

        self.marker = Marker(self.player_sprite.center_x, self.player_sprite.center_y, map_index)

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
        
        #if key == arcade.key.SPACE:
        #    print(int(self.player_sprite.center_x), " ", int(self.player_sprite.center_y), ",")
            
        if key == self.drift_key and (self.right_key in self.pressed_keys or self.left_key in self.pressed_keys):
            self.drifting = True
            self.top_speed *= 0.8
            self.speed *= 0.8
            self.acceleration *= 0.8
            self.handling /= 0.8
    
            if self.left_key in self.pressed_keys and self.right_key not in self.pressed_keys:
                self.player_sprite.angle += self.drift_offset
                    
            elif self.left_key not in self.pressed_keys and self.right_key in self.pressed_keys:
                self.player_sprite.angle -= self.drift_offset
                self.turing_left = False
        
        if self.drifting:
            if self.turing_left == True and key == self.right_key:
                self.player_sprite.angle -= 2*self.drift_offset
                self.turning_left = False
            if self.turing_left == False and key == self.left_key:
                self.player_sprite.angle += 2*self.drift_offset
                self.turning_left = True

    def key_released(self, key, modifiers):
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
        
        if key == self.drift_key and self.drifting:
            self.drifting = False
            self.speed += self.drift_boost*10
            self.boost_timer = self.drift_boost/2
            self.drift_boost = 0
            self.top_speed /= 0.8
            self.acceleration /= 0.8
            self.handling *= 0.8
            DRIFT_BOOST_SOUND.play_sound(0.2)
            
            self.direction = self.player_sprite.angle

    def update(self, multiplier):

        self.marker.check_distance(self.player_sprite.center_x, self.player_sprite.center_y)

        # movement calculations
        if self.forward_key in self.pressed_keys:
            self.speed += self.acceleration * multiplier
            if self.speed > self.top_speed:
                self.speed -= .35 * multiplier
        
        if self.break_key in self.pressed_keys:
            self.speed -= self.break_speed * multiplier
            if self.speed < -self.top_speed:
                self.speed += self.acceleration*3

        if self.speed > 0.1 or self.speed < -0.1:
            if self.right_key in self.pressed_keys:
                self.direction -= self.handling * multiplier
                self.player_sprite.angle -= self.handling * multiplier
                self.turing_left = False
            
            if self.left_key in self.pressed_keys:
                self.direction += self.handling * multiplier
                self.player_sprite.angle += self.handling * multiplier
                self.turing_left = True
        

        self.player_sprite.change_y = math.cos(math.radians(-self.direction)) * self.speed * multiplier * SCALE_MULTIPLIER
        self.player_sprite.change_x = math.sin(math.radians(-self.direction)) * self.speed * multiplier * SCALE_MULTIPLIER

        if self.speed > 0:
            self.speed -= 0.05 * multiplier
        if self.speed < 0:
            self.speed += 0.05 * multiplier
        
        if self.speed < 0.05 and self.speed > -0.05:
            self.speed = 0

        if self.drifting:
            if self.drift_boost < 1:
                self.drift_boost += 0.025 * multiplier
        
        # set boost to player
        self.boost_sprite.center_x = self.player_sprite.center_x
        self.boost_sprite.center_y = self.player_sprite.center_y
        self.boost_sprite.angle = self.player_sprite.angle

        if self.boost_timer > 0:
            self.boost_timer -= 0.01 * multiplier
            self.draw_boost = 1
        else:
            self.boost_timer = 0
            self.draw_boost = 0
        
        
        
    def draw(self):
        if self.boost_timer > 0:
            self.boost_sprite.draw(pixelated=True)
        self.player_sprite.draw(pixelated=True)
        arcade.draw_text(self.name, self.player_sprite.center_x, self.player_sprite.center_y+18*self.player_sprite.scale, arcade.color.WHITE, 12, anchor_x="center", font_name="Kenney Mini Square")
        if self.drifting:
            x, y = (self.player_sprite.center_x + 75*SCALE_MULTIPLIER), (self.player_sprite.center_y + 130*SCALE_MULTIPLIER)
            arcade.draw_circle_filled(x, y, 32*SCALE_MULTIPLIER, arcade.color.BLACK)
            arcade.draw_circle_filled(x, y, 30*self.drift_boost*SCALE_MULTIPLIER, (255, 255*(1-self.drift_boost), 0))
            arcade.draw_circle_outline(x, y, 35*SCALE_MULTIPLIER, arcade.color.EERIE_BLACK, 5*SCALE_MULTIPLIER)
        #self.marker.draw()

        #arcade.draw_circle_outline(self.player_sprite.center_x, self.player_sprite.center_y, 400 * MAP_SCALE_MULTIPLIER, arcade.color.YELLOW)

    
class OtherPlayer():
    def __init__(self, char_index, name):
        
        # player variables
        self.char_index = char_index
        self.player_sprite = arcade.Sprite()
        self.player_sprite.texture = arcade.load_texture("data/sprites/sprite_sheet.png", x = 32*self.char_index, y = 0, width = 32, height = 32)
        self.player_sprite.scale = 3.5 * SCALE_MULTIPLIER
        self.player_sprite.center_x = 0
        self.player_sprite.center_y = 0

        self.boost_sprite = arcade.Sprite()
        self.boost_sprite.texture = arcade.load_texture("data/sprites/sprite_sheet.png", x = 96 + 32*self.char_index, y = 0, width = 32, height = 40)
        self.boost_sprite.scale = self.player_sprite.scale
        self.boost_sprite.center_x = 0
        self.boost_sprite.center_y = 0

        self.name = name
        self.draw_boost = 0
        self.speed = 0

    def accept_data(self, x, y, angle, speed, boosting):
        self.player_sprite.center_x = x
        self.player_sprite.center_y = y
        self.player_sprite.angle = angle
        self.speed = speed
        print("speed is", speed)
        self.draw_boost = boosting

    def update(self, multiplier):

        self.player_sprite.change_y = math.cos(math.radians(-self.player_sprite.angle)) * self.speed * multiplier * SCALE_MULTIPLIER
        self.player_sprite.change_x = math.sin(math.radians(-self.player_sprite.angle)) * self.speed * multiplier * SCALE_MULTIPLIER
        self.player_sprite.center_y += self.player_sprite.change_y
        self.player_sprite.center_x += self.player_sprite.change_x
        # set boost to player
        self.boost_sprite.center_x = self.player_sprite.center_x
        self.boost_sprite.center_y = self.player_sprite.center_y
        self.boost_sprite.angle = self.player_sprite.angle

    def draw(self):
        if self.draw_boost == 1:
            self.boost_sprite.draw(pixelated=True)
        self.player_sprite.draw(pixelated=True)
        arcade.draw_text(self.name, self.player_sprite.center_x, self.player_sprite.center_y+18*self.player_sprite.scale, arcade.color.WHITE, 12, anchor_x="center", font_name="Kenney Mini Square")