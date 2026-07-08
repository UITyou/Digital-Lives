import os
import urllib.request

cv2_data_path = r"D:\python练习\coures_scraper\.venv\Lib\site-packages\cv2\data"

cascades = [
    ("haarcascade_frontalface_default.xml", "https://raw.githubusercontent.com/opencv/opencv/4.x/data/haarcascades/haarcascade_frontalface_default.xml"),
    ("haarcascade_eye.xml", "https://raw.githubusercontent.com/opencv/opencv/4.x/data/haarcascades/haarcascade_eye.xml"),
    ("haarcascade_smile.xml", "https://raw.githubusercontent.com/opencv/opencv/4.x/data/haarcascades/haarcascade_smile.xml"),
]

for filename, url in cascades:
    filepath = os.path.join(cv2_data_path, filename)
    print(f"下载 {filename}...")
    try:
        urllib.request.urlretrieve(url, filepath)
        print(f"  成功！")
    except Exception as e:
        print(f"  失败: {e}")

print("完成！")