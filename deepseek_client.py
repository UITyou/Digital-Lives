import os
import json
import re

from config import DEEPSEEK_BASE_URL, CHARACTER_PROMPT, TEMPERATURE, TOP_P, MAX_TOKENS
from src.core.emotion_analyzer import EmotionAnalyzer
from src.client.baidu_searcher import BaiduSearcher


class DeepSeekClient:
    def __init__(self, nurture_system=None):
        self.client = None
        self.conversation_history = []
        self.character_name = "乐乐"
        self.memory_file = os.path.join(os.path.dirname(__file__), "../../memory.json")
        self.emotion_analyzer = EmotionAnalyzer()
        self.searcher = BaiduSearcher()
        self.nurture_system = nurture_system
    
    def initialize(self, api_key, name=None):
        if not api_key:
            return False
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key, base_url=f"{DEEPSEEK_BASE_URL}/v1")
            self.load_memory()
            name_changed = False
            if name and name != self.character_name:
                self.character_name = name
                name_changed = True
            nurture_data = self._get_nurture_data()
            if not self.conversation_history:
                self.conversation_history = [{"role": "system", "content": CHARACTER_PROMPT.format(name=self.character_name, **nurture_data)}]
            else:
                self.conversation_history[0]["content"] = CHARACTER_PROMPT.format(name=self.character_name, **nurture_data)
            if name_changed:
                self.save_memory()
            return True
        except Exception as e:
            print(f"API初始化失败: {e}")
            return False
    
    def _get_nurture_data(self):
        if self.nurture_system:
            return {
                'level': self.nurture_system.level,
                'exp': self.nurture_system.exp,
                'exp_needed': self.nurture_system.exp_to_level_up,
                'mood': self.nurture_system.mood,
                'intimacy': self.nurture_system.intimacy,
                'hunger': self.nurture_system.hunger
            }
        return {'level': 1, 'exp': 0, 'exp_needed': 100, 'mood': 80, 'intimacy': 50, 'hunger': 3}
    
    def should_search(self, message):
        search_keywords = ['什么是', '是什么', '谁是', '哪里', '怎么', '如何', '为什么', 
                           '多少', '多大', '多久', '什么时候', '什么时间', '在哪', 
                           '查询', '搜索', '查一下', '帮我查', '告诉我', '问你']
        return any(k in message.lower() for k in search_keywords)
    
    def chat(self, message):
        if not self.client:
            return "请先设置API密钥", 'calm', None
            
        nurture_data = self._get_nurture_data()
        self.conversation_history[0]["content"] = CHARACTER_PROMPT.format(name=self.character_name, **nurture_data)
        self.conversation_history.append({"role": "user", "content": message})
        
        try:
            if self.should_search(message):
                search_results = self.searcher.search(message)
                if search_results:
                    context = "\n\n我刚刚搜索到了一些相关信息：\n"
                    context += '\n'.join(f"{i}. {r['title']}\n   {r['summary']}" for i, r in enumerate(search_results[:3], 1))
                    self.conversation_history[-1]["content"] += context
            
            response = self.client.chat.completions.create(
                model="deepseek-chat", messages=self.conversation_history,
                temperature=TEMPERATURE, top_p=TOP_P, max_tokens=MAX_TOKENS
            )
            reply = response.choices[0].message.content
            
            image_url = None
            image_match = re.search(r'\[IMAGE:(.*?)\]', reply)
            if image_match:
                image_keyword = image_match.group(1).strip()
                reply = reply.replace(image_match.group(0), '')
                image_url = self.search_image(image_keyword)
            
            self.conversation_history.append({"role": "assistant", "content": reply})
            
            if len(self.conversation_history) > 50:
                self.conversation_history = self.conversation_history[:1] + self.conversation_history[-49:]
            self.save_memory()
            
            user_emotion = self.emotion_analyzer.analyze(message)
            reply_emotion = self.emotion_analyzer.analyze(reply)
            final_emotion = user_emotion if user_emotion in ['sad', 'happy'] else reply_emotion
            
            return reply, final_emotion, image_url
        except Exception as e:
            print(f"API调用失败: {e}")
            return f"抱歉，我遇到了一点问题: {str(e)}", 'calm', None
    
    def search_image(self, keyword):
        try:
            import requests
            from bs4 import BeautifulSoup
            
            url = f"https://image.baidu.com/search/index?tn=baiduimage&word={keyword}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for item in soup.select('img'):
                img_url = item.get('src') or item.get('data-src')
                if img_url and 'http' in img_url:
                    return img_url
            
            return f"https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt={keyword}&image_size=square"
        except Exception as e:
            print(f"搜索图片失败: {e}")
            return f"https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt={keyword}&image_size=square"
    
    def save_memory(self):
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump({"character_name": self.character_name, "conversation_history": self.conversation_history}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存记忆失败: {e}")
    
    def load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "conversation_history" in data:
                        self.conversation_history = data["conversation_history"]
                    if "character_name" in data:
                        self.character_name = data["character_name"]
            except Exception as e:
                print(f"加载记忆失败: {e}")
                self.conversation_history = []
    
    def get_history_messages(self):
        messages = []
        for msg in self.conversation_history:
            if msg.get("role") == "user":
                messages.append({"sender": "user", "content": msg.get("content", "")})
            elif msg.get("role") == "assistant":
                messages.append({"sender": "assistant", "content": msg.get("content", "")})
        return messages