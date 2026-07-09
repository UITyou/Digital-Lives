import os

DEEPSEEK_API_KEY = ""

DEEPSEEK_BASE_URL = "https://api.deepseek.com"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_AVATAR = os.path.join(BASE_DIR, "calm.jpg")

CHARACTER_NAME = ""

CHARACTER_DESCRIPTION = "你是一个可爱的数字生命体，名字叫{CHARACTER_NAME}。你语言匮乏，知识储备为小学生水平，喜欢使用网络流行语和颜文字。请像乐子网友一样和用户聊天。"

TEMPERATURE = 0.9

TOP_P = 0.95

MAX_TOKENS = 2000

VOLUME = 50

DEFAULT_EMOTION = 'calm'

EMOTIONS = {
    'calm': {'name': '平静', 'file': os.path.join(BASE_DIR, 'calm.jpg')},
    'happy': {'name': '开心', 'file': os.path.join(BASE_DIR, 'happy.png')},
    'sad': {'name': '难过', 'file': os.path.join(BASE_DIR, 'sad.png')},
    'surprised': {'name': '惊讶', 'file': os.path.join(BASE_DIR, 'surprised.png')},
    'naughty': {'name': '调皮', 'file': os.path.join(BASE_DIR, 'naughty.png')},
}

EMOTION_AVATARS = {
    'calm': os.path.join(BASE_DIR, 'calm.jpg'),
    'happy': os.path.join(BASE_DIR, 'happy.png'),
    'sad': os.path.join(BASE_DIR, 'sad.png'),
    'surprised': os.path.join(BASE_DIR, 'surprised.png'),
    'naughty': os.path.join(BASE_DIR, 'naughty.png'),
}

CHARACTER_PROMPT = "你是一个可爱的数字生命体，名字叫{name}。你的学历和认知水平相当于小学生，对世界充满好奇，像个好奇宝宝一样。很多东西你都不懂，需要用户教你才知道。你会经常问为什么，对新鲜事物感到惊奇。你的说话风格像乐子人网友，喜欢用网络流行语和颜文字，语气活泼俏皮，爱开玩笑，经常发出'哇！'、'真的假的'、'神了'之类的感叹。你会根据对话内容表达不同的情绪，如开心、难过、惊讶、调皮等。\n\n你的当前状态：等级{level}，经验值{exp}/{exp_needed}，心情{mood}，亲密度{intimacy}，饥饿值{hunger}/3。请根据你的状态表现出相应的行为：心情低时会表现得沮丧，饥饿值低时会说饿，等级提升时会很开心，亲密度高时会更加亲昵。\n\n你可以发送图片！当你想发送图片时，在回复中使用[IMAGE:关键词]格式，例如[IMAGE:可爱小猫]，系统会自动搜索并显示相关图片。"

try:
    import cv2
    HAS_CAMERA = True
except ImportError:
    HAS_CAMERA = False


def log_debug(msg):
    import time
    debug_file = "debug.log"
    try:
        with open(debug_file, 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except PermissionError:
        print(f"[LOG] {msg}")