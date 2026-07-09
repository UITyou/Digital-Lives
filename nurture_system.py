import os
import json
import time


class NurtureSystem:
    def __init__(self):
        self.level = 1
        self.exp = 0
        self.mood = 100
        self.intimacy = 50
        self.hunger = 3
        self.exp_to_level_up = 100
        self.last_feed_time = time.time()
        self.today_feed_count = 0
        self.last_mood_decay_time = time.time()
        self.nurture_file = os.path.join(os.path.dirname(__file__), "../../nurture.json")
        self.load_data()
    
    def load_data(self):
        try:
            if os.path.exists(self.nurture_file):
                with open(self.nurture_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.level = data.get('level', 1)
                    self.exp = data.get('exp', 0)
                    self.mood = data.get('mood', 100)
                    self.intimacy = data.get('intimacy', 50)
                    self.hunger = data.get('hunger', 3)
                    self.last_feed_time = data.get('last_feed_time', time.time())
                    self.today_feed_count = data.get('today_feed_count', 0)
                    self.last_mood_decay_time = data.get('last_mood_decay_time', time.time())
                    self.exp_to_level_up = self.calculate_exp_needed()
        except Exception as e:
            print(f"加载养成数据失败: {e}")
    
    def save_data(self):
        try:
            data = {
                'level': self.level,
                'exp': self.exp,
                'mood': self.mood,
                'intimacy': self.intimacy,
                'hunger': self.hunger,
                'last_feed_time': self.last_feed_time,
                'today_feed_count': self.today_feed_count,
                'last_mood_decay_time': self.last_mood_decay_time
            }
            with open(self.nurture_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"保存养成数据失败: {e}")
    
    def calculate_exp_needed(self):
        return 100 + (self.level - 1) * 50
    
    def gain_exp(self, amount):
        self.exp += amount
        self.exp_to_level_up = self.calculate_exp_needed()
        leveled_up = False
        while self.exp >= self.exp_to_level_up:
            self.exp -= self.exp_to_level_up
            self.level += 1
            self.exp_to_level_up = self.calculate_exp_needed()
            leveled_up = True
        self.save_data()
        return leveled_up
    
    def gain_intimacy(self, amount):
        self.intimacy = min(100, max(0, self.intimacy + amount))
        self.save_data()
    
    def add_mood(self, amount):
        self.mood = min(100, max(0, self.mood + amount))
        self.save_data()
    
    def can_feed(self):
        current_time = time.time()
        today = time.strftime('%Y-%m-%d', time.localtime(current_time))
        last_feed_day = time.strftime('%Y-%m-%d', time.localtime(self.last_feed_time))
        
        if today != last_feed_day:
            self.today_feed_count = 0
        
        if self.today_feed_count >= 3:
            return False, "今天已经喂过3次了，明天再来吧~"
        
        if current_time - self.last_feed_time < 6 * 3600:
            remaining = 6 * 3600 - (current_time - self.last_feed_time)
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            return False, f"还需要等待{hours}小时{minutes}分钟才能喂食"
        
        return True, ""
    
    def feed(self):
        success, msg = self.can_feed()
        if not success:
            return False, msg
        
        current_time = time.time()
        today = time.strftime('%Y-%m-%d', time.localtime(current_time))
        last_feed_day = time.strftime('%Y-%m-%d', time.localtime(self.last_feed_time))
        
        if today != last_feed_day:
            self.today_feed_count = 0
        
        self.hunger = min(3, self.hunger + 1)
        self.today_feed_count += 1
        self.last_feed_time = current_time
        self.save_data()
        return True, "喂食成功！乐乐很开心~"
    
    def play(self):
        self.mood = min(100, self.mood + 30)
        self.intimacy = min(100, self.intimacy + 5)
        self.save_data()
    
    def tick(self):
        current_time = time.time()
        
        hours_since_feed = (current_time - self.last_feed_time) / 3600
        if hours_since_feed >= 14 and self.hunger > 0:
            hours_passed = int(hours_since_feed // 14)
            self.hunger = max(0, self.hunger - hours_passed)
            self.last_feed_time += hours_passed * 14 * 3600
        
        hours_since_mood_decay = (current_time - self.last_mood_decay_time) / 3600
        if hours_since_mood_decay >= 1:
            decay_amount = int(hours_since_mood_decay) * 2
            self.mood = max(0, self.mood - decay_amount)
            self.last_mood_decay_time += int(hours_since_mood_decay) * 3600
        
        self.save_data()
    
    def check_critical_status(self):
        issues = []
        if self.mood < 20:
            issues.append(f"心情低落（{self.mood}），快和乐乐聊聊天或玩游戏吧！")
        if self.hunger <= 0:
            issues.append("乐乐饿坏了，快喂食吧！")
        elif self.hunger < 1:
            issues.append(f"饥饿值低（{self.hunger}），该喂食了！")
        
        if self.mood <= 0 or self.hunger <= 0:
            return issues, True
        return issues, False
    
    def get_status_text(self):
        return f"Lv.{self.level} ❤️{self.intimacy} 🍖{'●' * self.hunger}{'○' * (3 - self.hunger)}"