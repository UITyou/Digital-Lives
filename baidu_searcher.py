import requests
from bs4 import BeautifulSoup


class BaiduSearcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def search(self, query, num_results=5):
        try:
            url = f"https://www.baidu.com/s?wd={query}"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            for item in soup.select('.result')[:num_results]:
                title = item.find('h3')
                content = item.find('div', class_='c-abstract')
                if title and content:
                    results.append({
                        'title': title.get_text(),
                        'summary': content.get_text()
                    })
            return results
        except Exception as e:
            print(f"搜索失败: {e}")
            return []