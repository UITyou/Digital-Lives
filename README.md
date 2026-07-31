# 数字生命

一个可爱的数字生命体桌面应用，具备聊天互动、养成系统、游戏功能和情绪识别等特性。

## 功能特性

- 🤖 **智能聊天** - 基于 DeepSeek API 实现的 AI 对话，支持网络搜索和图片发送
- 🎮 **养成系统** - 等级、经验、心情、亲密度、饥饿值等属性管理
- 🎲 **小游戏** - 猜谜语、画画、找不同三个互动游戏
- 🎭 **表情系统** - 根据情绪自动切换头像表情（平静、开心、难过、惊讶、调皮）
- 📷 **情绪识别** - 摄像头实时检测用户情绪和视线方向
- 🏀 **弹跳动画** - 智能体在桌面自由弹跳移动
- ⏸️ **暂停功能** - 点击暂停按钮可暂停/恢复弹跳
- 📱 **拖拽移动** - 支持拖拽移动智能体位置
- 📰 **自动消息** - 定时发送新闻和问候消息

## 目录结构

```
数字生命/
├── app.py                    # 主程序入口
├── config.py                 # 配置文件
├── memory.json               # 对话记忆数据
├── nurture.json              # 养成系统数据
├── sound/                    # 音效文件目录
│   ├── sound1.mp3
│   ├── sound2(1).mp3
│   └── sound3(1).mp3
├── src/                      # 源代码目录
│   ├── core/                 # 核心业务逻辑
│   │   ├── emotion_analyzer.py    # 情绪分析器
│   │   ├── game_system.py         # 游戏系统
│   │   └── nurture_system.py      # 养成系统
│   ├── client/               # 外部服务客户端
│   │   ├── baidu_searcher.py      # 百度搜索客户端
│   │   ├── camera_emotion_detector.py  # 摄像头情绪识别器
│   │   ├── deepseek_client.py     # DeepSeek API客户端
│   │   ├── news_fetcher.py        # 新闻获取器
│   │   └── sound_player.py        # 声音播放器
│   └── ui/                   # 用户界面组件
│       ├── avatar_widget.py       # 头像窗口（弹跳、拖拽）
│       ├── chat_window.py         # 聊天窗口
│       └── pause_button.py        # 暂停按钮
└── 表情图片/                 # 头像表情图片
    ├── calm.jpg
    ├── happy.png
    ├── sad.png
    ├── surprised.png
    └── naughty.png
```

## 安装依赖

```bash
pip install PySide6 Pillow opencv-python openai requests beautifulsoup4
```

## 启动方式

```bash
python app.py
```

## 配置说明

在 `config.py` 中配置以下参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| DEEPSEEK_API_KEY | DeepSeek API 密钥 | 空字符串 |
| CHARACTER_NAME | 数字生命名字 | 空字符串 |
| VOLUME | 音量大小 | 50 |
| DEFAULT_EMOTION | 默认情绪 | calm |

## 使用说明

1. **聊天** - 点击头像打开聊天窗口，输入消息并发送
2. **暂停弹跳** - 点击头像上方的 ✋ 按钮暂停/恢复弹跳
3. **移动位置** - 拖拽头像到目标位置
4. **喂食** - 在聊天窗口点击喂食按钮
5. **游戏** - 在聊天窗口点击游戏按钮选择小游戏
6. **设置** - 右键点击头像选择设置

## 模块职责

### 核心模块 (core)

- **nurture_system.py** - 管理养成属性（等级、经验、心情、亲密度、饥饿值），处理属性衰减和升级逻辑
- **game_system.py** - 实现三个小游戏（猜谜语、画画、找不同）
- **emotion_analyzer.py** - 根据文本内容分析情绪

### 客户端模块 (client)

- **deepseek_client.py** - 调用 DeepSeek API 进行对话，管理对话历史和记忆
- **baidu_searcher.py** - 调用百度搜索获取信息
- **camera_emotion_detector.py** - 使用 OpenCV 检测用户情绪和视线方向
- **news_fetcher.py** - 获取最新新闻资讯
- **sound_player.py** - 播放音效

### UI 模块 (ui)

- **avatar_widget.py** - 头像窗口，处理弹跳动画、拖拽移动、点击事件
- **chat_window.py** - 聊天窗口，显示消息、发送消息、显示养成状态
- **pause_button.py** - 暂停按钮，控制弹跳暂停/恢复

## 技术栈

- Python 3.14+
- PySide6 (GUI框架)
- OpenCV (摄像头情绪识别)
- Pillow (图像处理)
- DeepSeek API (AI对话)
- BeautifulSoup4 (网页解析)

## 团队成员
25智创何思思

- 需要配置 DeepSeek API Key 才能使用 AI 对话功能
- 摄像头功能需要 OpenCV 和可用的摄像头设备
- 养成系统数据会自动保存到 nurture.json
- 对话历史会自动保存到 memory.json
