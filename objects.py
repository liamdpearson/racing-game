import edit_file
import arcade
import math

class Marker():
    def __init__(self, player_x, player_y):
        self.total_checkpoints = 0
        self.checkpoint_index = 0

        self.int_for_sorting = 0

        self.dist_to_next_checkpoint = 1000

        # get the positions from the file and split them into a list
        self.positions = edit_file.get_positions().split(",")
        for i in range(len(self.positions)):
            self.positions[i] = self.positions[i].split()
        
        self.x = int(self.positions[self.checkpoint_index][0])
        self.y = int(self.positions[self.checkpoint_index][1])

        self.dist_between_cur_and_nxt_checkpoint = math.sqrt((self.x - player_x)**2 + (self.y - player_y)**2)


        
    
    def next_position(self, player_x, player_y):

        self.total_checkpoints += 1
        self.checkpoint_index += 1

        if self.checkpoint_index >= len(self.positions):
            self.checkpoint_index = 0
        self.x = int(self.positions[self.checkpoint_index][0])
        self.y = int(self.positions[self.checkpoint_index][1])

        self.dist_between_cur_and_nxt_checkpoint = math.sqrt((self.x - player_x)**2 + (self.y - player_y)**2)
    
    def check_distance(self, player_x, player_y):
        self.dist_to_next_checkpoint = math.sqrt((self.x - player_x)**2 + (self.y - player_y)**2)
        if self.dist_to_next_checkpoint < 400:
            self.next_position(player_x, player_y)
        
        self.int_for_sorting = int((self.total_checkpoints + 1 - self.dist_to_next_checkpoint/self.dist_between_cur_and_nxt_checkpoint)*100)
        
    

class Player():
    def __init__(self, pos_x, pos_y, car_stats, keybinds, char_index, name):
        super().__init__()
        
        # player variables
        self.char_index = char_index
        self.player_sprite = arcade.Sprite()
        self.player_sprite.texture = arcade.load_texture("sprites/sprite_sheet.png", x = 32*self.char_index, y = 0, width = 32, height = 32)
        self.player_sprite.scale = 3.5
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

        self.marker = Marker(self.player_sprite.center_x, self.player_sprite.center_y)

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

    def update(self, multiplier):

        self.marker.check_distance(self.player_sprite.center_x, self.player_sprite.center_y)

        # movement calculations
        if self.forward_key in self.pressed_keys:
            self.speed += self.acceleration * multiplier
            if self.speed > self.top_speed:
                self.speed -= self.acceleration*3
        
        if self.break_key in self.pressed_keys:
            self.speed -= self.break_speed * multiplier
            if self.speed < -self.top_speed:
                self.speed += self.acceleration*3

        if self.speed > 0.1 or self.speed < -0.1:
            if self.right_key in self.pressed_keys:
                self.direction -= self.handling * multiplier
                self.player_sprite.angle -= self.handling * multiplier
            
            if self.left_key in self.pressed_keys:
                self.direction += self.handling * multiplier
                self.player_sprite.angle += self.handling * multiplier
        

        self.player_sprite.change_y = math.cos(math.radians(-self.direction)) * self.speed * multiplier
        self.player_sprite.change_x = math.sin(math.radians(-self.direction)) * self.speed * multiplier

        if self.speed > 0:
            self.speed -= 0.05 * multiplier
            
        
        
        
    def draw(self):
        self.player_sprite.draw(pixelated=True)
        arcade.draw_text(self.name, self.player_sprite.center_x, self.player_sprite.center_y+18*self.player_sprite.scale, arcade.color.WHITE, 12, anchor_x="center", font_name="Kenney Mini Square")

    
class OtherPlayer():
    def __init__(self, pos_x, pos_y, char_index, name):
        
        # player variables
        self.char_index = char_index
        self.player_sprite = arcade.Sprite()
        self.player_sprite.texture = arcade.load_texture("sprites/sprite_sheet.png", x = 32*self.char_index, y = 0, width = 32, height = 32)
        self.player_sprite.scale = 3.5
        self.player_sprite.center_x = pos_x
        self.player_sprite.center_y = pos_y

        self.name = name
        
    def draw(self):
        self.player_sprite.draw(pixelated=True)

        arcade.draw_text(self.name, self.player_sprite.center_x, self.player_sprite.center_y+18*self.player_sprite.scale, arcade.color.WHITE, 12, anchor_x="center", font_name="Kenney Mini Square")