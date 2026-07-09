class EmotionAnalyzer:
    def __init__(self):
        self.keywords = {
            'sad': ['难过', '伤心', '失望', '沮丧', '哭', '难受', '痛苦', '累', '烦', '郁闷', '绝望', '可怜'],
            'surprised': ['惊讶', '哇', '天哪', '真的吗', '没想到', '居然', '突然', '震惊'],
            'naughty': ['调皮', '捉弄', '恶作剧', '开玩笑', '逗', '恶搞', '捣蛋', '坏'],
            'happy': ['开心', '高兴', '快乐', '笑', '哈哈', '好棒', '喜欢', '爱', '不错', '赞', '厉害', '太棒', '优秀']
        }
    
    def analyze(self, text):
        for emotion, keywords in self.keywords.items():
            if any(keyword in text for keyword in keywords):
                return emotion
        return 'calm'