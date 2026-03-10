import arcade

class SoundManager:
    def __init__(self, file_name):
        self.sound = arcade.load_sound("data/sounds/" + file_name)
        self.sound_player = None
    
    def play_sound(self, volume=1.0):
        if not self.sound_player or not self.sound_player.playing:
            self.sound_player = arcade.play_sound(self.sound, volume = volume)
        
    def force_play_sound(self, volume=1.0):
        self.sound_player = arcade.play_sound(self.sound, volume = volume)