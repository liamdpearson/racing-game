
import arcade
import data.scripts.soundmanager as soundmanager


#SCREEN_WIDTH, SCREEN_HEIGHT = arcade.window_commands.get_display_size()
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 1000

SCALE_MULTIPLIER = SCREEN_WIDTH/2560
MAP_SCALE_MULTIPLIER = 1.25 * SCALE_MULTIPLIER

DIST_FROM_CORNER = 100

DRIFT_BOOST_SOUND = soundmanager.SoundManager("drift_boost.wav")
DRIFT_BOOST_SOUND.play_sound(0)
SPEED_BOOST_SOUND = soundmanager.SoundManager("speed_boost.wav")
SPEED_BOOST_SOUND.play_sound(0)