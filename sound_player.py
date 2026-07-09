import os
import sys
import random


class SoundPlayer:
    def __init__(self, volume=50):
        self.volume = volume
        self.wmp = None
        self._init_player()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    def _init_player(self):
        try:
            import win32com.client
            self.wmp = win32com.client.Dispatch("WMPlayer.OCX")
        except ImportError:
            try:
                from comtypes.client import CreateObject
                self.wmp = CreateObject("WMPlayer.OCX")
            except ImportError:
                self.wmp = None
    
    def play_sound(self, sound_type):
        if self.wmp is None:
            return
        
        sound_files = {
            'greeting': os.path.join(self.base_dir, 'sound', 'sound1.mp3'),
            'goodbye': os.path.join(self.base_dir, 'sound', 'sound2(1).mp3'),
            'happy': os.path.join(self.base_dir, 'sound', 'sound3(1).mp3')
        }
        
        sound_file = sound_files.get(sound_type)
        if sound_file and os.path.exists(sound_file):
            try:
                self.wmp.URL = sound_file
                self.wmp.settings.volume = self.volume
                self.wmp.controls.play()
            except Exception as e:
                print(f"播放声音失败: {e}")
    
    def play_random_happy_sound(self):
        if self.wmp is None:
            return
        
        happy_sounds = [
            os.path.join(self.base_dir, 'sound', 'sound1.mp3'),
            os.path.join(self.base_dir, 'sound', 'sound2(1).mp3'),
            os.path.join(self.base_dir, 'sound', 'sound3(1).mp3')
        ]
        
        valid_sounds = [s for s in happy_sounds if os.path.exists(s)]
        if valid_sounds:
            sound_file = random.choice(valid_sounds)
            try:
                self.wmp.URL = sound_file
                self.wmp.settings.volume = self.volume
                self.wmp.controls.play()
            except Exception as e:
                print(f"播放随机声音失败: {e}")