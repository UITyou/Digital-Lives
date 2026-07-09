import random
import requests
from bs4 import BeautifulSoup


class NewsFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_news(self):
        try:
            url = "https://news.baidu.com/"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_items = []
            for item in soup.select('a.title')[:5]:
                title = item.get_text()
                if title and len(title) > 5:
                    news_items.append(title)
            
            return news_items[:3]
        except Exception as e:
            print(f"获取新闻失败: {e}")
            return [
                "今日天气晴朗，适合外出活动",
                "人工智能技术持续发展",
                "数字生命系统更新啦！"
            ]
    
    def get_opinion(self, news_item):
        opinions = [
            f"这个新闻很有意思呢！你觉得呢？",
            f"看到这条新闻，我想到了很多...",
            f"这条新闻让我有点好奇，你怎么看？",
            f"这个话题很有趣，我们可以聊聊！"
        ]
        return random.choice(opinions)